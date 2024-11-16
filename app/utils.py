import re

def is_valid_email(email):
    email_regex = r"^[a-zA-Z0-9._%+-]+@go\.stockton\.edu$"
    return bool(re.match(email_regex, email))

def is_valid_name(name):
    name_regex = r"^[A-Za-z]+ [A-Za-z]+$" 
    return bool(re.match(name_regex, name))

def is_valid_password(password):
    password_regex = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$"
    return bool(re.match(password_regex, password))
