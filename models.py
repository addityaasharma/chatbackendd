from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Admin(db.Model):
    __tablename__ = "Admin"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class User(db.Model):
    __tablename__ = "User"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    username = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    phoneNumber = db.Column(db.String(255))
    password = db.Column(db.String(255), nullable=False)
    panel = db.relationship("UserPanel", back_populates="user", uselist=False)


class UserPanel(db.Model):
    __tablename__ = "UserPanel"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    userId = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)
    userChatId = db.relationship("UserChat", back_populates="userpanel")
    userChatGroupID = db.relationship("ChatGroup", uselist=True, backref="userpanel")


class UserChat(db.Model):
    __tablename__ = "UserChat"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    panelID = db.Column(db.Integer, db.ForeignKey("UserPanel.id"), nullable=False)
    userID = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)
    recieverID = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)
    chat = db.Column(db.String(255), nullable=False)
    chat_at = db.Column(db.DateTime, default=datetime.utcnow)


class ChatGroup(db.Model):
    __tablename__ = "ChatGroup"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    chatTitle = db.Column(db.String(255), nullable=False)
    chatId = db.Column(db.Integer, db.ForeignKey("UserChat.id"), nullable=False)
    panelId = db.Column(db.Integer, db.ForeignKey("UserPanel.id"), nullable=False)
    chat_at = db.Column(db.DateTime, default=datetime.utcnow)
