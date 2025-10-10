from functools import wraps
from flask import redirect, url_for, session, request, flash
from flask_login import LoginManager, current_user
from models import User

# Initialize Flask-Login
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            session["next_url"] = request.url
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def require_role(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                session["next_url"] = request.url
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login'))
            
            # Admin can access all routes
            if current_user.role == 'admin':
                return f(*args, **kwargs)
            
            if current_user.role != role:
                flash(f'Access denied. This page requires {role} privileges.', 'error')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator