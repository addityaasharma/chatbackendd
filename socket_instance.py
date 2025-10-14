# from flask_socketio import SocketIO, join_room, emit
# import threading, time, random, datetime

# socketio = SocketIO(cors_allowed_origins="*", async_mode='gevent')

# fake_users = ["Alice", "Bob", "Charlie", "David"]
# fake_messages = [
#     "Hello everyone!",
#     "How’s it going?",
#     "Anyone online?",
#     "That’s awesome!",
#     "Good morning!",
# ]


# def generate_fake_chats():
#     """Background thread that emits fake messages every few seconds."""
#     while True:
#         time.sleep(random.randint(5, 15))  # wait 5–15 seconds
#         room = "group_1"  # target room (or loop through rooms dynamically)
#         user = random.choice(fake_users)
#         message = random.choice(fake_messages)

#         chat_payload = {
#             "id": random.randint(1000, 9999),
#             "sender": user,
#             "receiver": "all",
#             "chat": message,
#             "chat_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         }

#         socketio.emit("receive_message", chat_payload, room=room)
#         print(f"Fake message sent in {room}: {user}: {message}")

# threading.Thread(target=generate_fake_chats, daemon=True).start()


# @socketio.on("join")
# def on_join(data):
#     room = data.get("room")
#     user = data.get("user")  # optional, if you want to know who joined
#     if room:
#         join_room(room)
#         print(f"User joined room: {room}")

#         emit(
#             "user_joined",
#             {"room": room, "message": f"{user or 'A user'} joined {room}"},
#             room=room,
#             include_self=False,  # don’t send it back to the joining user
#         )

from flask_socketio import SocketIO, join_room, emit
import threading
import time
import random
import datetime

socketio = SocketIO(cors_allowed_origins="*", async_mode="gevent")

# fake_users = [
#     "Anant",
#     "Shraddha",
#     "Himanshi",
#     "Purnima",
#     "Bhoomika",
#     "Jaspreet",
#     "Ayush",
#     "Rahul",
#     "Neeraj",
#     "Mayank",
#     "Dhiraj",
#     "SnehDeep",
#     "Mihir",
#     "Ritika",
#     "Adarsh",
#     "Ashwini",
# ]
# fake_messages = [
#     "Yeh kya hai",
#     "Arey ek naya event aane walaa hai",
#     "Event me suna mai ki macbook milega?",
#     "Haa, koi product purchase krne pr event ki ticket bhi free mil rhi hai",
#     "Maine purchase kia hai mujhe bhi mili hai",
#     "Par ye event hai kya..?",
#     "Iske bare me to shaam 6 bje update aata h group me bole",
#     "Achaa..",
#     "Sahi hai yaar",
#     "Event kaha hai?",
#     "6 baje isi me update aayega..",
#     "Kal join tha to bataye the",
#     "6 baje bahut sare log rehte hai",
#     "Its really fun",
#     "shaam 6 baje..?",
#     "Haa 6 se 8 ki bich.",
# ]

active_rooms = ["group_1", "group_2", "group_3"]


# def generate_fake_chats():
#     """Background thread that emits fake messages to all rooms."""
#     while True:
#         time.sleep(random.randint(2, 3))
#         # time.sleep(1)

#         for room in active_rooms:
#             user = random.choice(fake_users)
#             message = random.choice(fake_messages)

#             chat_payload = {
#                 "id": random.randint(1000, 9999),
#                 "sender": user,
#                 "receiver": "all",
#                 "chat": message,
#                 "chat_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#             }

#             socketio.emit("receive_message", chat_payload, room=room)
#             print(f"[Fake] {user} in {room}: {message}")


# threading.Thread(target=generate_fake_chats, daemon=True).start()


# -----------------------
# SocketIO join event
# -----------------------
@socketio.on("join")
def on_join(data):
    room = data.get("room")
    user = data.get("user")
    if room:
        join_room(room)

        if room not in active_rooms:
            active_rooms.append(room)

        emit(
            "user_joined",
            {"room": room, "message": f"{user or 'A user'} joined {room}"},
            room=room,
            include_self=False,
        )
