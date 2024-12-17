from flask import render_template, redirect, url_for, request, flash, session
from authlib.integrations.base_client.errors import OAuthError
from flask_login import login_user, login_required, logout_user, current_user
from app.extensions import db, limiter, mail, google
import time
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
from app.models.user import User
from app.auth import auth_bp


# Rate limit error handler
# TODO Make redirect go off current page
@auth_bp.errorhandler(429)
def rate_limit_exceeded(e):
    email = session.get("email")
    flash("Your have exceeded the allowed number of email requests. Please wait and try again", "danger")
    return redirect(url_for('auth.login', email=email))

@limiter.limit("3 per minute; 10 per hour")
def send_verification_email_limit(email):
    token = generate_verification_token(email)
    verification_url = url_for('auth.verify_email', token=token, _external=True)
    send_verification_email(mail, email, verification_url)

@limiter.limit("3 per minute; 10 per hour")
def send_reset_email_limit(email):
    token = generate_reset_email(email)
    reset_url = url_for('auth.reset_email', token=token, _external=True)
    send_reset_email(mail, email, reset_url)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.my_groups'))
    
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if fields are provided
        if not email or not password:
            flash("All fields are required", "danger")
            return redirect(url_for('auth.login'))
        
        # Validate email format
        if not is_valid_email(email):
            flash("Please use a valid Stockton Email address.", "danger")
            return redirect(url_for('auth.login'))

        # Get user info from db and make instance of Users
        user = User.query.filter_by(email=email).first()

        # Check if user exists in db
        if not user:
            flash("Invalid email or password", 'danger')
            return redirect(url_for('auth.login'))
        
        # Detect Google SSO accounts
        if user.is_google_user:
            flash("Invalid email or password", 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.check_password(password):
                flash("Invalid email or password", 'danger')
                return redirect(url_for('auth.login'))
        
        if not user.is_verified:
            session["email"] = user.email
            send_verification_email_limit(user.email)
            return redirect(url_for('auth.verify_page'))

        login_user(user)
        return redirect(url_for('main.my_groups'))

    return render_template("login.html")

@auth_bp.route('/login/google')
def login_google():
    redirect_uri = url_for('auth.authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@auth_bp.route('/login/callback')
def authorize():
    try:
        token = google.authorize_access_token()
        user_info = google.get('userinfo').json()

        if not isinstance(user_info, dict):
            flash("Failed to fetch user information from Google. Please try again.", "danger")
            return redirect(url_for('auth.login'))

        # Grab user details
        email = user_info['email']
        name = user_info['name']
        google_id = user_info['id']
        domain = user_info.get('hd')


        # TODO Redirect user back to original page
        # Only allow Stockton emails
        if not domain or domain != "go.stockton.edu":
            flash("Only Stockton Google Accounts are allowed.", "danger")
            return redirect(url_for('auth.login'))

        # Check if user already exists
        user = User.query.filter_by(email=email).first()

        if user:
            if user.is_google_user:
                # Log in Google user
                login_user(user)
                return redirect(url_for('main.my_groups'))
            else:
                # Existing Manual Account
                flash("This email is registered manually. Please log in using your Stockton email and password.", "danger")
                return redirect(url_for('auth.login'))
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
            
            return redirect(url_for('main.my_groups'))
    except OAuthError:
        flash("Authorization failed or was denied. Please try again.", "danger")
        return redirect(url_for('auth.login'))
    

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.my_groups'))
    
    if request.method == "POST":
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not name or not email or not password or not confirm_password:
            flash("All fields are required.", "danger")
            return redirect(url_for('auth.register'))
        
        if not is_valid_name(name):
            flash("Please enter your full name (first and last name).", "danger")
            return redirect(url_for('auth.register'))
        
        if not is_valid_email(email):
            flash("Please use a valid Stockton Email address.", "danger")
            return redirect(url_for('auth.register'))
        
        if password != confirm_password:
            flash("Passwords do not match. Please re-enter your password", "danger")
            return redirect(url_for('auth.register'))
        
        email_exists = User.query.filter_by(email=email).first()
        if email_exists:
            flash("Email is already registered.", 'danger')
            return redirect(url_for('auth.register'))
        
        if not is_valid_password(password):
            flash("Password must be at least 8 characters long and include one letter, one number, and one special character.", "danger")
            return redirect(url_for('auth.register'))
        

        new_user = User(name=name, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()

        send_verification_email_limit(email)

        # Save email to session
        session["reg_email"] = email

        return redirect(url_for('auth.verify_page'))
        
    return render_template("register.html")

@auth_bp.route("/verify-page")
def verify_page():
    email = session.get("reg_email")
    if not email:
        flash("Session expired or no email found.", "danger")
        return redirect(url_for('auth.login'))
    
    return render_template('verify.html', email=email)

@auth_bp.route("/verify-email/<token>")
def verify_email(token):
    email = confirm_verification_token(token)

    # Clear Session
    session.pop('reg_email', None)

    # Confirm token
    if not email:
        flash("The verification link is invalid or has expired", "danger")
        return redirect(url_for('auth.login'))
    
    # Find user in database
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('auth.register'))
    
    if user.is_verified:
        flash("Your email is already verified", "info")
        return redirect(url_for('auth.login'))
    
    user.is_verified = True
    db.session.commit()

    flash("Your email has been verified! You can now log in", "success")
    return redirect(url_for('auth.login'))

@auth_bp.route("/resend-verification", methods=['POST'])
def resend_verification():
    email = session.get('reg_email')

    if not email:
        flash("Session expired or no email found. Please register again.", "danger")
        return redirect(url_for('auth.register'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Not account found with this email. Please register first.", "danger")
        return redirect(url_for('auth.register'))
    
    # Generate and send new verification email
    send_verification_email_limit(email)

    flash("A new verification link has been sent to your email.", "success")
    return redirect(url_for('auth.verify_page'))


@auth_bp.route("/reset", methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get("email")

        if not email:
            flash("You must enter an email", "danger")
            return redirect(url_for('auth.reset_password'))
        
        if not is_valid_email(email):
            flash("Please use a valid Stockton Email address.", "danger")
            return redirect(url_for('auth.reset_password'))
        
        user = User.query.filter_by(email=email).first()

        if user is None:
            time.sleep(2.92)
        elif user.is_google_user == 0:
            send_reset_email_limit(user.email)
        else:
            # Fake load time to prevent email enumeration
            time.sleep(2.92)

        session["reset_email"] = email
        
        return redirect(url_for('auth.check_email'))

    return render_template("reset.html")


@auth_bp.route("/check-email")
def check_email():
    email = session.get("reset_email")
    if not email:
        flash("Session expired", "danger")
        return redirect(url_for('auth.reset_password'))
    
    return render_template('check-email.html', email=email)

@auth_bp.route("/reset-email/<token>")
def reset_email(token):
    email = confirm_reset_token(token)

    # Confirm token
    if not email:
        flash("The reset link is invalid or has expired.", "danger")
        return redirect(url_for('auth.login'))
    
    session.pop("reset_email", None)
    session['reset_verified_email'] = email

    return redirect(url_for('auth.change_password'))

@auth_bp.route('/resend-reset', methods=['POST'])
def resend_reset():
    email = session.get('reset_email')
    
    if not email:
        flash("Session expired", "danger")
        return redirect(url_for('auth.reset_password'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        time.sleep(2.75)
    else:
        send_reset_email_limit(user.email)

    flash(f"If {email} is an email on file, we have sent an email to help you reset your password.", "success")
    return redirect(url_for('auth.check_email'))



@auth_bp.route("/change-password", methods=['GET', 'POST'])
def change_password():
    if not session.get("reset_verified_email"):
            flash("Unauthorized access or session expired.", "danger")
            return redirect(url_for('auth.reset_password'))
    
    if request.method == "POST":
        reset_email = session.get('reset_verified_email')

        if not reset_email:
            flash("Unauthorized access or session expired.", "danger")
            return redirect(url_for('auth.reset_password'))

        new_password = request.form.get("new-password")
        confirm_password = request.form.get("new-confirm-password")

        if new_password != confirm_password:
            flash("Passwords do not match", "danger")
            return redirect(url_for('auth.change_password'))
        
        user = User.query.filter_by(email=reset_email).first()
        if user.check_password(new_password):
            flash("Password must not match recent passwords.", "danger")
            return redirect(url_for('auth.change_password'))
        
        if not is_valid_password(new_password):
            flash("Password must be at least 8 characters long and include one letter, one number, and one special character.", "danger")
            return redirect(url_for('auth.change_password'))
        
        session.pop('reset_verified_email', None)
        user.set_password(new_password)
        db.session.commit()

        flash("Password updated successfully.", "success")
        return redirect(url_for('auth.login'))
    

    return render_template("change-password.html")
    

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))