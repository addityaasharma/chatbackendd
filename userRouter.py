from flask import Blueprint, jsonify, request, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, UserPanel, UserChat
from datetime import datetime, timedelta
from socket_instance import socketio
import jwt

userBP = Blueprint("user", __name__)


@userBP.route("/signup", methods=["POST"])
def signup():
    data = request.json or {}
    required_fields = ["username", "email", "password", "phoneNumber", "name"]

    if not all(field in data and data[field] for field in required_fields):
        return (
            jsonify({"status": "error", "message": "Please fill all the details"}),
            400,
        )

    try:
        existing_user = User.query.filter(
            (User.username == data["username"]) | (User.email == data["email"])
        ).first()

        if existing_user:
            return jsonify({"status": "error", "message": "User already exists"}), 409

        hashed_pass = generate_password_hash(data["password"], method="pbkdf2:sha256")

        new_user = User(
            username=data["username"],
            name=data["name"],
            email=data["email"],
            phoneNumber=data["phoneNumber"],
            password=hashed_pass,
        )
        db.session.add(new_user)
        db.session.flush()

        user_panel = UserPanel(userId=new_user.id)
        db.session.add(user_panel)

        db.session.commit()

        token_payload = {
            "userId": new_user.id,
            "exp": datetime.utcnow() + timedelta(days=7),
        }
        token = jwt.encode(
            token_payload, current_app.config["SECRET_KEY"], algorithm="HS256"
        )

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "User created successfully",
                    "token": token,
                    "user": {
                        "id": new_user.id,
                        "username": new_user.username,
                        "email": new_user.email,
                        "phoneNumber": new_user.phoneNumber,
                    },
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {"status": "error", "message": "Internal Server Error", "error": str(e)}
            ),
            500,
        )


@userBP.route("/login", methods=["POST"])
def login():
    data = request.json
    requiredFields = ["email", "password"]

    # Ensure required fields are provided
    if not all(field in data and data[field] for field in requiredFields):
        return (
            jsonify(
                {"status": "error", "message": "Please provide both email and password"}
            ),
            400,
        )

    try:
        user = User.query.filter_by(email=data["email"]).first()

        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        # Check password
        if not check_password_hash(user.password, data["password"]):
            return jsonify({"status": "error", "message": "Invalid password"}), 401

        token_payload = {
            "user_id": user.id,
            "exp": datetime.utcnow() + timedelta(days=7),
        }

        token = jwt.encode(
            token_payload, current_app.config.get("SECRET_KEY"), algorithm="HS256"
        )

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Login successful",
                    "token": token,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "phoneNumber": user.phoneNumber,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": "Internal Server Error", "error": str(e)}
            ),
            500,
        )


@userBP.route("/chat", methods=["POST"])
def send_chat():
    data = request.json
    requiredFields = ["userID", "message"]

    if not all(field in data and data[field] for field in requiredFields):
        return jsonify({
            "status": "error",
            "message": "Please provide userID and message"
        }), 400

    try:
        user = User.query.get(data["userID"])
        if not user:
            return jsonify({
                "status": "error",
                "message": "Sender not found"
            }), 404

        receiver_id = data.get("receiverID")
        if receiver_id == "all":
            receiver_id = None

        new_chat = UserChat(
            panelID=user.panel.id,
            userID=user.id,
            recieverID=receiver_id,
            chat=data["message"],
            chat_at=datetime.utcnow()
        )
        db.session.add(new_chat)
        db.session.commit()

        chat_payload = {
            "id": new_chat.id,
            "sender": user.username,
            "receiver": "all" if receiver_id is None else receiver_id,
            "chat": new_chat.chat,
            "chat_at": new_chat.chat_at.strftime("%Y-%m-%d %H:%M:%S")
        }

        socketio.emit("receive_message", chat_payload)

        return jsonify({
            "status": "success",
            "message": "Chat sent successfully",
            "chat": chat_payload
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Internal Server Error",
            "error": str(e)
        }), 500

#  GET /chats - all chats
# GET /chats?userID=1 - chats sent by user 
# GET /chats?receiverID=all - public chats
# GET /chats?receiverID=2  -  private chats to user
        
@userBP.route("/chat", methods=["GET"])
def get_chats():
    try:
        user_id = request.args.get("userID", type=int)   
        receiver_id = request.args.get("receiverID")
        query = UserChat.query

        if user_id:
            query = query.filter_by(userID=user_id)

        if receiver_id:
            if receiver_id == "all":
                query = query.filter_by(recieverID=None)
            else:
                query = query.filter_by(recieverID=int(receiver_id))

        chats = query.order_by(UserChat.chat_at.asc()).all()

        chat_list = []
        for chat in chats:
            sender = User.query.get(chat.userID)
            chat_list.append({
                "id": chat.id,
                "sender": sender.username if sender else "Unknown",
                "receiver": "all" if chat.recieverID is None else chat.recieverID,
                "chat": chat.chat,
                "chat_at": chat.chat_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        return jsonify({
            "status": "success",
            "chats": chat_list
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Internal Server Error",
            "error": str(e)
        }), 500