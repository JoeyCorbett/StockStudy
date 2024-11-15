from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import re

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key_here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///StockStudy.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = 'login'

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()

    @app.route('/')
    @login_required
    def index():
        return render_template('index.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        if request.method == "POST":
            print("Post")

        return render_template("login.html")
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        if request.method == "POST":
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            if not name or not email or not password or not confirm_password:
                flash("All fields are required.", "danger")
                return redirect(url_for('register'))
        
            if password != confirm_password:
                flash("Passwords do not match.", "danger")
                return redirect(url_for('register'))
            
            name_regex = r"^[A-Za-z]+ [A-Za-z]+$" 
            if not re.match(name_regex, name):
                flash("Please enter your full name (first and last name).", "danger")
                return redirect(url_for('register'))
            
            email_regex = r"^[a-zA-Z0-9._%+-]+@go\.stockton\.edu$"
            if not re.match(email_regex, email):
                flash("Please use a valid Stockton Email address.", "danger")
                return redirect(url_for('register'))
            
            password_regex = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$"
            if not re.match(password_regex, password):
                flash("Password must be at least 8 characters long and include one letter, one number, and one special character.", "danger")
            
            user = User.query.filter_by(email=email).first()
            if user:
                flash("Email is already registered.", 'danger')
                return redirect(url_for('register'))
            
        return render_template("register.html")
    
    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('login'))


    return app