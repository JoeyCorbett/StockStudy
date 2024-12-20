import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_login import LoginManager
from flask_limiter import Limiter
from authlib.integrations.flask_client import OAuth
from flask import request

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()

# Manually extracts client's real IP
def get_forwarded_ip():
    forwarded_for = request.headers.get("X-Forwarded-For", None)
    if forwarded_for:
        return forwarded_for.split(",")[0]
    return request.remote_addr 

if os.getenv("FLASK_ENV") == "production":
    STORAGE_URI = os.getenv("REDISCLOUD_URL")
else:
    STORAGE_URI = "memory://"

limiter = Limiter(
    key_func=get_forwarded_ip,
    default_limits=["1000 per day", "200 per hour"],
    storage_uri=STORAGE_URI
)

oauth = OAuth()
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    access_token_url='https://oauth2.googleapis.com/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid email profile'},
    jwks_uri='https://www.googleapis.com/oauth2/v3/certs',
)
