from flask import Flask
from config import Config
from models import db
from flask_migrate import Migrate
from userRouter import userBP

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)

# routes
app.register_blueprint(userBP, url_prefix="/user")

@app.route('/')
def method_name():
    return "Hello"

if __name__ == "__main__":
    app.run(debug=True)
