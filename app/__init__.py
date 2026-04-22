from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object("config")
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = "login"  # type: ignore

from app import routes, models  # noqa: E402, F401
from app.seed import register_commands
register_commands(app)
