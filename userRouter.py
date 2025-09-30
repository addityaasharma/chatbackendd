from flask import Blueprint, jsonify, request, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from zoneinfo import ZoneInfo
from models import db, User, UserPanel, UserChat, Post, ChatGroup
from datetime import datetime, timedelta
from socket_instance import socketio
import jwt, os
import pytz
from redis import Redis
from flask import request, jsonify, current_app
from otp_utils import generate_otp, send_otp


userBP = Blueprint("user", __name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
india = pytz.timezone("Asia/Kolkata")

REDIS_URL = os.getenv("REDIS_URL")
redis = Redis.from_url(REDIS_URL)

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_unique_username(base_username):
    username = base_username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}{counter}"
        counter += 1
    return username


@userBP.route("/signup", methods=["POST"])
def signup():
    data = request.json or {}
    required_fields = ["email", "password", "phoneNumber", "name"]

    if not required_fields[0]:
        return jsonify({"status": "success"})

    for field in required_fields:
        if not data.get(field):
            return jsonify({"status": "error", "message": f"{field} is required"}), 400

    googleToken = data.get("googleToken")

    try:
        if googleToken:
            response = requests.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={googleToken}"
            )
            if response.status_code != 200:
                return (
                    jsonify({"status": "error", "message": "Invalid Google Token"}),
                    400,
                )

            user_info = response.json()
            data["email"] = user_info.get("email", data["email"])
            data["name"] = user_info.get("name", data["name"])

        base_username = data["email"].split("@")[0]
        username = generate_unique_username(base_username)

        existing_user = User.query.filter_by(email=data["email"]).first()
        if existing_user:
            return jsonify({"status": "error", "message": "User already exists"}), 409

        hashed_pass = generate_password_hash(data["password"], method="pbkdf2:sha256")

        new_user = User(
            username=username,
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


@userBP.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.json
    email = data.get("email")

    if not email:
        return jsonify({"status": "error", "message": "Please provide email"}), 400

    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            return (
                jsonify(
                    {"status": "error", "message": "No user found with this email"}
                ),
                404,
            )

        otp = generate_otp()
        otp_sent = send_otp(email, otp)

        if not otp_sent:
            return jsonify({"status": "error", "message": "Failed to send OTP"}), 500

        redis.setex(f"forgot_password:{email}", 300, otp)

        return jsonify({"status": "success", "message": "OTP sent successfully"}), 200

    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": "Internal Server Error", "error": str(e)}
            ),
            500,
        )


@userBP.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.json or {}
    otp = data.get("otp")
    email = data.get("email")
    new_password = data.get("new_password")

    if not all([email, otp, new_password]):
        return jsonify({
            "status": "error",
            "message": "Please provide email, OTP, and new password"
        }), 400

    try:
        # Get OTP from Redis
        stored_otp = redis.get(f"forgot_password:{email}")
        if not stored_otp:
            return jsonify({
                "status": "error",
                "message": "OTP expired or not found, please request a new one"
            }), 400

        stored_otp = stored_otp.decode("utf-8")
        if stored_otp != str(otp):
            return jsonify({
                "status": "error",
                "message": "Incorrect OTP, please try again"
            }), 400

        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"status": "error", "message": "No user found"}), 404

        # Update password
        user.password = generate_password_hash(new_password)
        db.session.commit()

        # Clear OTP
        redis.delete(f"forgot_password:{email}")

        return jsonify({
            "status": "success",
            "message": "Password reset successfully"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Internal Server Error"
            # "error": str(e)  # Uncomment only in dev
        }), 500



@userBP.route("/chat", methods=["POST"])
def send_chat():
    data = request.json
    requiredFields = ["userID", "message"]

    if not all(field in data and data[field] for field in requiredFields):
        return (
            jsonify(
                {"status": "error", "message": "Please provide userID and message"}
            ),
            400,
        )

    group_id = data.get("groupID")

    try:
        user = User.query.get(data["userID"])
        if not user:
            return jsonify({"status": "error", "message": "Sender not found"}), 404

        receiver_id = data.get("receiverID")
        if receiver_id == "all":
            receiver_id = None

        new_chat = UserChat(
            panelID=user.panel.id,
            userID=user.id,
            recieverID=receiver_id,
            groupID=group_id,
            chat=data["message"],
            chat_at=datetime.now(india),
        )
        db.session.add(new_chat)
        db.session.commit()

        chat_payload = {
            "id": new_chat.id,
            "sender": user.username,
            "receiver": "all" if receiver_id is None else receiver_id,
            "chat": new_chat.chat,
            "chat_at": new_chat.chat_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

        socketio.emit("receive_message", chat_payload, room=f"group_{group_id}")

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Chat sent successfully",
                    "chat": chat_payload,
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


# @userBP.route("/chat", methods=["GET"])
# def get_group_chats():
#     try:
#         group_id = request.args.get("groupID", type=int)

#         if not group_id:
#             return (
#                 jsonify({"status": "error", "message": "Please provide a groupID"}),
#                 400,
#             )

#         chats = (
#             UserChat.query.filter_by(groupID=group_id)
#             .order_by(UserChat.chat_at.asc())
#             .all()
#         )

#         chat_list = []
#         for chat in chats:
#             sender = User.query.get(chat.userID)
#             chat_time_ist = chat.chat_at.astimezone(india)
#             chat_list.append(
#                 {
#                     "id": chat.id,
#                     "sender": sender.username if sender else "Unknown",
#                     "groupID": chat.groupID,
#                     "chat": chat.chat,
#                     "chat_at": chat_time_ist.strftime("%Y-%m-%d %H:%M:%S"),
#                 }
#             )

#         return jsonify({"status": "success", "chats": chat_list}), 200

#     except Exception as e:
#         return (
#             jsonify(
#                 {
#                     "status": "error",
#                     "message": "Internal Server Error",
#                     "error": str(e),
#                 }
#             ),
#             500,
#         )


@userBP.route("/chat", methods=["GET"])
def get_group_chats():
    try:
        group_id = request.args.get("groupID", type=int)

        if not group_id:
            return (
                jsonify({"status": "error", "message": "Please provide a groupID"}),
                400,
            )

        chats = (
            UserChat.query.filter_by(groupID=group_id)
            .order_by(UserChat.chat_at.desc())
            .limit(100)
            .all()
        )

        chats.reverse()

        chat_list = []
        for chat in chats:
            sender = User.query.get(chat.userID)
            chat_time_ist = chat.chat_at.astimezone(india)
            chat_list.append(
                {
                    "id": chat.id,
                    "sender": sender.username if sender else "Unknown",
                    "groupID": chat.groupID,
                    "chat": chat.chat,
                    "chat_at": chat_time_ist.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        return jsonify({"status": "success", "chats": chat_list}), 200

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Internal Server Error",
                    "error": str(e),
                }
            ),
            500,
        )


@userBP.route("/allusers", methods=["GET"])
def get_all_users():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        search = request.args.get("search", "", type=str)

        query = User.query

        if search:
            query = query.filter(
                (User.name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
            )

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        users = pagination.items

        user_list = [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phoneNumber": user.phoneNumber,
            }
            for user in users
        ]

        return (
            jsonify(
                {
                    "status": "success",
                    "page": page,
                    "per_page": per_page,
                    "total_users": pagination.total,
                    "total_pages": pagination.pages,
                    "users": user_list,
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


@userBP.route("/post", methods=["POST"])
def create_post():
    try:
        file = request.files.get("image")
        link = request.form.get("link")

        if not file or file.filename == "":
            return (
                jsonify({"status": "error", "message": "Image file is required"}),
                400,
            )

        if not allowed_file(file.filename):
            return jsonify({"status": "error", "message": "Invalid file type"}), 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        new_post = Post(image=filename, link=link)
        db.session.add(new_post)
        db.session.commit()

        image_url = request.host_url + "uploads/" + filename

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Post created successfully",
                    "post": {
                        "id": new_post.id,
                        "image": image_url,
                        "link": link,
                    },
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@userBP.route("/post", methods=["GET"])
def get_latest_post():
    try:
        latest_post = Post.query.order_by(Post.id.desc()).first()

        if not latest_post:
            return jsonify({"status": "error", "message": "No posts found"}), 404

        image_url = request.host_url + "uploads/" + latest_post.image

        return (
            jsonify(
                {
                    "status": "success",
                    "post": {
                        "id": latest_post.id,
                        "image": image_url,
                        "link": latest_post.link,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@userBP.route("/posts", methods=["GET"])
def get_all_posts():
    try:
        posts = Post.query.order_by(Post.id.desc()).all()

        if not posts:
            return jsonify({"status": "error", "message": "No posts found"}), 404

        posts_data = []
        for post in posts:
            image_url = request.host_url + "uploads/" + post.image
            posts_data.append({"id": post.id, "image": image_url, "link": post.link})

        return jsonify({"status": "success", "posts": posts_data}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@userBP.route("/group", methods=["POST"])
def create_group():
    try:
        data = request.json
        chat_title = data.get("chatTitle")

        if not chat_title:
            return jsonify({"status": "error", "message": "chatTitle is required"}), 400

        new_group = ChatGroup(chatTitle=chat_title)
        db.session.add(new_group)
        db.session.commit()

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Group created successfully",
                    "group": {
                        "id": new_group.id,
                        "chatTitle": new_group.chatTitle,
                        "created_at": new_group.created_at.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    },
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@userBP.route("/group", methods=["GET"])
def get_groups():
    try:
        groups = ChatGroup.query.order_by(ChatGroup.created_at.asc()).all()

        group_list = []
        for group in groups:
            group_list.append(
                {
                    "id": group.id,
                    "chatTitle": group.chatTitle,
                    "created_at": group.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "chat_count": len(group.chats),
                }
            )

        return jsonify({"status": "success", "groups": group_list}), 200

    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": "Internal Server Error", "error": str(e)}
            ),
            500,
        )
