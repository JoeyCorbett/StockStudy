import os
from flask import Flask, render_template, redirect, url_for, request, flash, session
from authlib.integrations.flask_client import OAuth
from authlib.integrations.base_client.errors import OAuthError
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from app.utils import (
    is_valid_email,
    is_valid_name,
    is_valid_password,
    generate_verification_token,
    confirm_verification_token,
    send_verification_email,
    generate_reset_email,
    confirm_reset_token,
    send_reset_email,
)
import time
from dotenv import load_dotenv
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()

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

     # Mail configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    mail.init_app(app)

    # Initialize Flask-Limiter
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        # TODO Replace with appropriate storage for prod
        storage_uri="memory://",
    )

    # Rate limit error handler
    # TODO Make redirect go off current page
    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        email = session.get("email")
        flash("Your have exceeded the allowed number of email requests. Please wait and try again", "danger")
        return redirect(url_for('login', email=email))
    
    @limiter.limit("1 per minute; 5 per hour")
    def send_verification_email_limit(email):
        token = generate_verification_token(email)
        verification_url = url_for('verify_email', token=token, _external=True)
        send_verification_email(mail, email, verification_url)

    @limiter.limit("1 per minute; 5 per hour")
    def send_reset_email_limit(email):
        token = generate_reset_email(email)
        reset_url = url_for('reset_email', token=token, _external=True)
        send_reset_email(mail, email, reset_url)

    login_manager.login_view = 'login'
    login_manager.login_message = None

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
                flash("Invalid email or password", 'danger')
                return redirect(url_for('login'))
            
            if not user.check_password(password):
                 flash("Invalid email or password", 'danger')
                 return redirect(url_for('login'))
            
            if not user.is_verified:
                session["email"] = user.email
                send_verification_email_limit(user.email)
                return redirect(url_for('verify_page'))

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
        try:
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
        except OAuthError:
            flash("Authorization failed or was denied. Please try again.", "danger")
            return redirect(url_for('login'))
        
    
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

            send_verification_email_limit(email)

            # Save email to session
            session["reg_email"] = email

            return redirect(url_for('verify_page'))
            
        return render_template("register.html")
    
    @app.route("/verify-page")
    def verify_page():
        email = session.get("reg_email")
        if not email:
            flash("Session expired or no email found.", "danger")
            return redirect(url_for('login'))
        
        return render_template('verify.html', email=email)

    @app.route("/verify-email/<token>")
    def verify_email(token):
        email = confirm_verification_token(token)

        # Clear Session
        session.pop('reg_email', None)

        # Confirm token
        if not email:
            flash("The verification link is invalid or has expired", "danger")
            return redirect(url_for('login'))
        
        # Find user in database
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("User not found.", "danger")
            return redirect(url_for('register'))
        
        if user.is_verified:
            flash("Your email is already verified", "info")
            return redirect(url_for('login'))
        
        user.is_verified = True
        db.session.commit()

        flash("Your email has been verified! You can now log in", "success")
        return redirect(url_for('login'))

    @app.route("/resend-verification", methods=['POST'])
    def resend_verification():
        email = session.get('reg_email')

        if not email:
            flash("Session expired or no email found. Please register again.", "danger")
            return redirect(url_for('register'))
        
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Not account found with this email. Please register first.", "danger")
            return redirect(url_for('register'))
        
        # Generate and send new verification email
        send_verification_email_limit(email)

        flash("A new verification link has been sent to your email.", "success")
        return redirect(url_for('verify_page'))
    

    @app.route("/reset", methods=['GET', 'POST'])
    def reset_password():
        if request.method == 'POST':
            email = request.form.get("email")

            if not email:
                flash("You must enter an email", "danger")
                return redirect(url_for('reset_password'))
            
            if not is_valid_email(email):
                flash("Please use a valid Stockton Email address.", "danger")
                return redirect(url_for('reset_password'))
            
            
            user = User.query.filter_by(email=email).first()
            if user:
                send_reset_email_limit(user.email)
            else:
                # Fake load time to prevent email enumeration
                time.sleep(2.92)

            session["reset_email"] = email
            
            return redirect(url_for('check_email'))

        return render_template("reset.html")
    
    
    @app.route("/check-email")
    def check_email():
        email = session.get("reset_email")
        if not email:
            flash("Session expired", "danger")
            return redirect(url_for('reset_password'))
        
        return render_template('check-email.html', email=email)
    
    @app.route("/reset-email/<token>")
    def reset_email(token):
        email = confirm_reset_token(token)

        # Confirm token
        if not email:
            flash("The reset link is invalid or has expired.", "danger")
            return redirect(url_for('login'))
        
        session.pop("reset_email", None)
        session['reset_verified_email'] = email
    
        return redirect(url_for('change_password'))
    
    @app.route('/resend-reset', methods=['POST'])
    def resend_reset():
        email = session.get('reset_email')
        
        if not email:
            flash("Session expired", "danger")
            return redirect(url_for('reset_password'))
        
        user = User.query.filter_by(email=email).first()
        if not user:
            time.sleep(2.75)
        else:
            send_reset_email_limit(user.email)

        flash(f"If {email} is an email on file, we have sent an email to help you reset your password.", "success")
        return redirect(url_for('check_email'))


    
    @app.route("/change-password", methods=['GET', 'POST'])
    def change_password():
        if not session.get("reset_verified_email"):
                flash("Unauthorized access or session expired.", "danger")
                return redirect(url_for('reset_password'))
        
        if request.method == "POST":
            reset_email = session.get('reset_verified_email')

            if not reset_email:
                flash("Unauthorized access or session expired.", "danger")
                return redirect(url_for('reset_password'))

            new_password = request.form.get("new-password")
            confirm_password = request.form.get("new-confirm-password")

            if new_password != confirm_password:
                flash("Passwords do not match", "danger")
                return redirect(url_for('change_password'))
            
            user = User.query.filter_by(email=reset_email).first()
            if user.check_password(new_password):
                flash("Password must not match recent passwords.", "danger")
                return redirect(url_for('change_password'))
            
            if not is_valid_password(new_password):
                flash("Password must be at least 8 characters long and include one letter, one number, and one special character.", "danger")
                return redirect(url_for('change_password'))
            
            session.pop('reset_verified_email', None)
            user.set_password(new_password)
            db.session.commit()

            flash("Password updated successfully.", "success")
            return redirect(url_for('login'))
        
    
        return render_template("change-password.html")
        

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "success")
        return redirect(url_for('login'))


    return app