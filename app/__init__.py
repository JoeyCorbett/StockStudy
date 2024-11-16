import os
from flask import Flask, render_template, redirect, url_for, request, flash
from authlib.integrations.flask_client import OAuth
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from app.utils import is_valid_email, is_valid_name, is_valid_password
from dotenv import load_dotenv
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///StockStudy.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    oauth = OAuth(app)

    #Google OAuth configuration
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
            email = request.form.get("email")
            password = request.form.get("password")

            # Check if fields are provided
            if not email or not password:
                flash("All fields are required", "danger")
                return redirect(url_for('login'))
            
            # Validate email format
            if not is_valid_email(email):
                flash("Please use a valid Stockton Email address.", "danger")
                return redirect(url_for('login'))

            # Get user info from db and make instance of Users
            user = User.query.filter_by(email=email).first()

            # Check if user exists in db
            if not user:
                flash("Invalid email or password", 'danger')
                return redirect(url_for('login'))
            
            # Detect Google SSO accounts
            if user.is_google_user:
                flash("This account is linked to Google. Please log in with Google.", "danger")
                return redirect(url_for('login'))
            
            if not user.check_password(password):
                 flash("Invalid email or password", 'danger')
                 return redirect(url_for('login'))

            # TODO: check if user is verified before logging in
            

            # TODO: Account locking

            login_user(user)
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(url_for('index'))

        return render_template("login.html")
    
    @app.route('/login/google')
    def login_google():
        redirect_uri = url_for('authorize', _external=True)
        return google.authorize_redirect(redirect_uri)
    
    @app.route('/login/callback')
    def authorize():
        token = google.authorize_access_token()
        user_info = google.get('userinfo').json()

        if not isinstance(user_info, dict):
            flash("Failed to fetch user information from Google. Please try again.", "danger")
            return redirect(url_for('login'))

        # Grab user details
        email = user_info['email']
        name = user_info['name']
        google_id = user_info['id']
        domain = user_info.get('hd')


        # TODO Redirect user back to original page
        # Only allow Stockton emails
        if not domain or domain != "go.stockton.edu":
            flash("Only Stockton Google Accounts are allowed.", "danger")
            return redirect(url_for('login'))

        # Check if user already exists
        user = User.query.filter_by(email=email).first()

        if user:
            if user.is_google_user:
                # Log in Google user
                login_user(user)
                flash(f"Welcome, {user.name}!", "success")
                return redirect(url_for('index'))
            else:
                # Existing Manual Account
                flash("This email is registered manually. Please log in using your Stockton email and password.", "danger")
                return redirect(url_for('login'))
        else:
            new_user = User(
                name=name,
                email=email,
                google_id=google_id,
                is_google_user=True,
                is_verified=True,
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash(f"Welcome, {new_user.name}!", "success")
            return redirect(url_for('index'))
        
    
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
            
            if not is_valid_name(name):
                flash("Please enter your full name (first and last name).", "danger")
                return redirect(url_for('register'))
            
            if not is_valid_email(email):
                flash("Please use a valid Stockton Email address.", "danger")
                return redirect(url_for('register'))
            
            if password != confirm_password:
                flash("Passwords do not match. Please re-enter your password", "danger")
                return redirect(url_for('register'))
            
            email_exists = User.query.filter_by(email=email).first()
            if email_exists:
                flash("Email is already registered.", 'danger')
                return redirect(url_for('register'))
            
            if not is_valid_password(password):
                flash("Password must be at least 8 characters long and include one letter, one number, and one special character.", "danger")
                return redirect(url_for('register'))
            

            new_user = User(name=name, email=email)
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()

            flash("Registration successful! Log in below", "success")
            return redirect(url_for('login'))
            
        return render_template("register.html")
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "success")
        return redirect(url_for('login'))


    return app