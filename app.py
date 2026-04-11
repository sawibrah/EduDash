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

# Set SESSION_SECRET with fallback for development
# FIX: Added fallback default value "dev-secret-key-change-in-production" to prevent 
# RuntimeError when SESSION_SECRET environment variable is not set
# For production, always set the SESSION_SECRET environment variable to a secure key
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1) # needed for url_for to generate with https

# Configure Babel
app.config['LANGUAGES'] = {
    'en': 'English',
    'fr': 'Français'
}
app.config['BABEL_DEFAULT_LOCALE'] = 'fr'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'

babel = Babel()

def get_locale():
    from flask import session
    return session.get('language', app.config['BABEL_DEFAULT_LOCALE'])

# Initialize Babel with the app
babel.init_app(app, locale_selector=get_locale)

# Enable CSRF protection globally
csrf = CSRFProtect(app)

# Configure the database
# FIX: Added fallback SQLite database for development with absolute path
# Using absolute path on Windows prevents sqlite3.OperationalError: unable to open database file
# SQLite requires the full path format: sqlite:////absolute/path/to/db.db (4 slashes on Windows)
# For production, set the DATABASE_URL environment variable to your database connection string
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'edudash.db')
default_db_uri = f"sqlite:///{db_path.replace(chr(92), '/')}"  # Convert backslashes to forward slashes
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", default_db_uri)
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
    # FIX: Create instance directory if it doesn't exist
    # SQLite requires the parent directory to exist before creating the database file
    # This prevents sqlite3.OperationalError: unable to open database file
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    
    # Make sure to import the models here or their tables won't be created
    import models  # noqa: F401
    
    # Initialize Flask-Login
    from auth import login_manager
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    
    db.create_all()
    logging.info("Database tables created")

from blueprints import register_blueprints  # noqa: E402

register_blueprints(app)

from gmail_auth import init_google_oauth  # noqa: E402

init_google_oauth(app)
