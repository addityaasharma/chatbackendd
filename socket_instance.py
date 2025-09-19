# from flask_socketio import SocketIO, join_room

# socketio = SocketIO(cors_allowed_origins="*")

# @socketio.on("join")
# def on_join(data):
#     room = data.get("room")
#     if room:
#         join_room(room)
#         print(f"User joined room: {room}")


from flask_socketio import SocketIO, join_room, emit

socketio = SocketIO(cors_allowed_origins="*")

@socketio.on("join")
def on_join(data):
    room = data.get("room")
    user = data.get("user")  # optional, if you want to know who joined
    if room:
        join_room(room)
        print(f"User joined room: {room}")
        
        emit(
            "user_joined",
            {"room": room, "message": f"{user or 'A user'} joined {room}"},
            room=room,
            include_self=False,  # don’t send it back to the joining user
        )
