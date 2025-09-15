from flask import Flask
from config import Config
from models import db
from flask_cors import CORS
from flask_migrate import Migrate
from userRouter import userBP

app = Flask(__name__)
app.config.from_object(Config)

CORS(
    app,
    resources={r"/*": {"origins": "http://localhost:5173"}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)

db.init_app(app)
migrate = Migrate(app, db)

app.register_blueprint(userBP, url_prefix="/user")


@app.route("/")
def method_name():
    return "Hello"


if __name__ == "__main__":
    app.run(debug=True)
