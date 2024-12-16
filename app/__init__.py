import os
from flask import Flask, render_template
from datetime import timedelta
from dotenv import load_dotenv
from app.extensions import db, migrate, bcrypt, login_manager, mail, limiter, oauth
from flask_migrate import upgrade
from app.auth import auth_bp
from app.main import main_bp
from app.models.user import User
from app.models.study_group import StudyGroup
from app.models.membership_requests import GroupJoinRequest

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    db_url = os.getenv('DATABASE_URL', 'sqlite:///StockStudy.db')
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
  #  app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)

    # Initialize Flask-Limiter
    limiter.init_app(app)

     # Mail configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    oauth.init_app(app)
    limiter.init_app(app)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')

    login_manager.login_view = 'auth.login'
    login_manager.login_message = None

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    with app.app_context():
        try:
            upgrade()
        except Exception as e:
            print(f"Database upgrade failed: {e}")


    return app