from flask import Blueprint, jsonify, request, current_app
from werkzeug.security import generate_password_hash
from models import db, User, UserPanel
from datetime import datetime, timedelta
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