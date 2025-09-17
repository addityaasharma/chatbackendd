# from flask import Flask
# from config import Config
# from models import db
# from flask_cors import CORS
# from flask_migrate import Migrate
# from userRouter import userBP
# from socket_instance import socketio

# app = Flask(__name__)
# app.config.from_object(Config)

# CORS(
#     app,
#     resources={r"/*": {"origins": "*"}},
#     supports_credentials=True,
#     allow_headers=["Content-Type", "Authorization"],
#     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
# )

# db.init_app(app)
# migrate = Migrate(app, db)

# app.register_blueprint(userBP, url_prefix="/user")
# socketio.init_app(app, cors_allowed_origins="*")


# @app.route("/")
# def method_name():
#     return "Hello"


# if __name__ == "__main__":
#     socketio.run(app, host="0.0.0.0", port=5000, debug=True)


# import eventlet
# eventlet.monkey_patch()

# from flask import Flask
# from config import Config
# from models import db
# from flask_cors import CORS
# from flask_migrate import Migrate
# from userRouter import userBP
# from socket_instance import socketio

# app = Flask(__name__)
# app.config.from_object(Config)

# CORS(
#     app,
#     resources={r"/*": {"origins": "*"}},
#     supports_credentials=True,
#     allow_headers=["Content-Type", "Authorization"],
#     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
# )

# db.init_app(app)
# migrate = Migrate(app, db)

# app.register_blueprint(userBP, url_prefix="/user")
# socketio.init_app(app, cors_allowed_origins="*")


# @app.route("/")
# def method_name():
#     return "Hello"


# if __name__ == "__main__":
#     import os
#     port = int(os.environ.get("PORT", 5000))
#     socketio.run(app, host="0.0.0.0", port=port, debug=True)




import eventlet
eventlet.monkey_patch()

from flask import Flask
from config import Config
from models import db
from flask_cors import CORS
from flask_migrate import Migrate
from userRouter import userBP
from socket_instance import socketio

app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)

# Database setup
db.init_app(app)
migrate = Migrate(app, db)

# Blueprints
app.register_blueprint(userBP, url_prefix="/user")

# SocketIO
socketio.init_app(app, cors_allowed_origins="*")

@app.route("/")
def index():
    return "Hello from Flask SocketIO!"

# Use Eventlet for Render
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))  # Use Render's assigned port
    # debug=False in production
    socketio.run(
        app,
        host="0.0.0.0",
        port=port,
        debug=False,       # Set False on Render
        use_reloader=False, # Avoid multiple processes that break sockets
        allow_unsafe_werkzeug=True # Required for Eventlet 0.33+ with Flask 2.3+
    )
