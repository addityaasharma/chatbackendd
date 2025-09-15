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
    email = db.Column(db.String(255), unique=True, nullable=False)
    phoneNumber = db.Column(db.String(255))
    password = db.Column(db.String(255), nullable=False)
    panel = db.relationship("UserPanel", back_populates="user", uselist=False)
    sent_chats = db.relationship(
        "UserChat", foreign_keys="UserChat.userID", back_populates="sender"
    )
    received_chats = db.relationship(
        "UserChat", foreign_keys="UserChat.recieverID", back_populates="receiver"
    )


class UserPanel(db.Model):
    __tablename__ = "UserPanel"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    userId = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)
    user = db.relationship("User", back_populates="panel")
    chats = db.relationship("UserChat", back_populates="panel")
    chat_groups = db.relationship("ChatGroup", back_populates="panel")


class UserChat(db.Model):
    __tablename__ = "UserChat"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    panelID = db.Column(db.Integer, db.ForeignKey("UserPanel.id"), nullable=False)
    userID = db.Column(db.Integer, db.ForeignKey("User.id"), nullable=False)
    recieverID = db.Column(
        db.Integer, db.ForeignKey("User.id"), nullable=False
    )
    chat = db.Column(db.String(255), nullable=False)
    chat_at = db.Column(db.DateTime, default=datetime.utcnow)
    panel = db.relationship("UserPanel", back_populates="chats")
    sender = db.relationship("User", foreign_keys=[userID], back_populates="sent_chats")
    receiver = db.relationship(
        "User", foreign_keys=[recieverID], back_populates="received_chats"
    )
    groups = db.relationship("ChatGroup", back_populates="chat")


class ChatGroup(db.Model):
    __tablename__ = "ChatGroup"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    chatTitle = db.Column(db.String(255), nullable=False)
    chatId = db.Column(db.Integer, db.ForeignKey("UserChat.id"), nullable=False)
    panelId = db.Column(db.Integer, db.ForeignKey("UserPanel.id"), nullable=False)
    chat_at = db.Column(db.DateTime, default=datetime.utcnow)
    chat = db.relationship("UserChat", back_populates="groups")
    panel = db.relationship("UserPanel", back_populates="chat_groups")