import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_wtf.csrf import CSRFProtect
from flask_babel import Babel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)

# Enforce SESSION_SECRET is set
if not os.environ.get("SESSION_SECRET"):
    raise RuntimeError("SESSION_SECRET environment variable is not set. Application cannot start without a secret key for session security.")

app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1) # needed for url_for to generate with https

# Configure Babel
app.config['LANGUAGES'] = {
    'en': 'English',
    'fr': 'Français'
}
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'

babel = Babel()

def get_locale():
    # Check if user has set a language preference
    from flask import session, request
    if 'language' in session:
        return session['language']
    # Try to get language from request headers
    return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

# Initialize Babel with the app
babel.init_app(app, locale_selector=get_locale)

# Enable CSRF protection globally
csrf = CSRFProtect(app)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_size": 10,
    "max_overflow": 20,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Enforce file upload size limit (50MB)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import models  # noqa: F401
    
    # Initialize Flask-Login
    from auth import login_manager
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'
    
    db.create_all()
    logging.info("Database tables created")
