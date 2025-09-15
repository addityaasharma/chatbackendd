from flask import Blueprint, jsonify, request, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from models import *
from datetime import datetime, timedelta
import jwt

userBP = Blueprint("user", __name__)


@userBP.route("/signup", methods=["POST"])
def signup():
    data = request.json
    requiredFields = ["username", "email", "password", "phoneNumber"]

    if not all(field in data and data[field] for field in requiredFields):
        return (
            jsonify({"status": "error", "message": "Please fill all the details"}),
            400,
        )

    try:
        existingUser = User.query.filter(
            (User.username == data["username"]) | (User.email == data["email"])
        ).first()

        if existingUser:
            return jsonify({"status": "error", "message": "User already exist"}), 409

        hashed_pass = generate_password_hash(data["password"], method="sha256")
        new_user = User(
            username=data["username"],
            name=data.get("name"),
            email=data.get("email"),
            phoneNumber=data.get("phoneNumber"),
            password=hashed_pass,
        )

        db.session.add(new_user)
        db.session.commit()

        user_panel = UserPanel(userId=new_user.id)
        db.session.add(user_panel)
        db.session.commit()
        
        token_payload = {
            "newUser" : new_user.id,
            "exp" : datetime.utcnow() + timedelta(days=7)
        }
        
        token = jwt.encode(token_payload, current_app.config.get("SECRET_KEY"), algorithm = "HS256")

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "User created successfully",
                    "token" : token
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
