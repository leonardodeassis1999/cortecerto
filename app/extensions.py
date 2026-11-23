"""Extensões do Flask criadas aqui para evitar importação circular."""
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

login_manager.login_view = "auth.login"  # T01 Login
login_manager.login_message = "Sessão expirada, faça login"  # SE12
login_manager.login_message_category = "warning"
