import os
import re
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from datetime import datetime, timezone, timedelta

def is_valid_email(email):
    email_regex = r"^[a-zA-Z0-9._%+-]+@go\.stockton\.edu$"
    return bool(re.match(email_regex, email))

def is_valid_name(name):
    name_regex = r"^[A-Za-z]+ [A-Za-z]+$" 
    return bool(re.match(name_regex, name))

def is_valid_password(password):
    password_regex = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$"
    return bool(re.match(password_regex, password))

def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(os.getenv('SECRET_KEY'))
    token =  serializer.dumps(email, salt='email-confirmation-salt')
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    return token, expires_at

def generate_reset_email(email):
    serializer = URLSafeTimedSerializer(os.getenv('SECRET_KEY'))
    token =  serializer.dumps(email, salt='password-reset-salt')
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    return token, expires_at


def confirm_verification_token(token):
    serializer = URLSafeTimedSerializer(os.getenv('SECRET_KEY'))
    try:
        email = serializer.loads(token, salt='email-confirmation-salt')
        return email
    except: 
        return None
    
def confirm_reset_token(token):
    serializer = URLSafeTimedSerializer(os.getenv('SECRET_KEY'))
    try:
        email = serializer.loads(token, salt='password-reset-salt')
        return email
    except: 
        return None
    
# TODO Customize Email prompt
    
def send_verification_email(mail, email, verification_url):
    msg = Message(
        "Verify Your Email",
        sender=os.getenv('MAIL_USERNAME'),
        recipients=[email],
        body=f"Please click the link to verify your email: {verification_url}"
    )
    mail.send(msg)

def send_reset_email(mail, email, reset_url):
    msg = Message(
        "Reset Your Password",
        sender=os.getenv('MAIL_USERNAME'),
        recipients=[email],
        body=f"Please click the link to reset your password: {reset_url}"
    )
    mail.send(msg)