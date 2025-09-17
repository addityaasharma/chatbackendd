from flask_socketio import SocketIO, join_room

socketio = SocketIO(cors_allowed_origins="*")

@socketio.on("join")
def on_join(data):
    room = data.get("room")
    if room:
        join_room(room)
        print(f"User joined room: {room}")