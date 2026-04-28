from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from flask_socketio import SocketIO

db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()
socketio = SocketIO()