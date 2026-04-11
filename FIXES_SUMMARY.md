# EduDash Application Fixes Summary

## Overview
This document outlines all the fixes applied to resolve startup errors and make the application fully functional.

---

## 1. SESSION_SECRET Environment Variable Issue

### Error
```
RuntimeError: SESSION_SECRET environment variable is not set. Application cannot start without a secret key for session security.
```

### Fix Applied
**File:** `app.py` (Lines 23-26)

```python
# Set SESSION_SECRET with fallback for development
# FIX: Added fallback default value "dev-secret-key-change-in-production" to prevent 
# RuntimeError when SESSION_SECRET environment variable is not set
# For production, always set the SESSION_SECRET environment variable to a secure key
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
```

### What Changed
- Changed from strict requirement (raises RuntimeError) to a fallback default value
- Development can now run without explicitly setting SESSION_SECRET
- Production deployments MUST set SESSION_SECRET environment variable for security

### How to Use
**Development:**
```powershell
python .\main.py
```

**Production:**
```powershell
$env:SESSION_SECRET = "your-secure-random-key-here"
python .\main.py
```

---

## 2. DATABASE_URL Environment Variable Issue

### Error
```
RuntimeError: Either 'SQLALCHEMY_DATABASE_URI' or 'SQLALCHEMY_BINDS' must be set.
```

### Fix Applied
**File:** `app.py` (Lines 52-58)

```python
# Configure the database
# FIX: Added fallback SQLite database for development with absolute path
# Using absolute path on Windows prevents sqlite3.OperationalError: unable to open database file
# SQLite requires the full path format: sqlite:////absolute/path/to/db.db (4 slashes on Windows)
# For production, set the DATABASE_URL environment variable to your database connection string
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'edudash.db')
default_db_uri = f"sqlite:///{db_path.replace(chr(92), '/')}"  # Convert backslashes to forward slashes
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", default_db_uri)
```

### What Changed
- Added fallback to SQLite database for development
- Uses absolute paths to prevent database file access issues on Windows
- Converts Windows backslashes to forward slashes (SQLite URI requirement)
- Database file created at: `instance/edudash.db`

### How to Use
**Development (SQLite):**
```powershell
python .\main.py
```

**Production (PostgreSQL/MySQL):**
```powershell
$env:DATABASE_URL = "postgresql://user:password@host:port/database"
python .\main.py
```

---

## 3. Database Directory Does Not Exist

### Error
```
sqlite3.OperationalError: unable to open database file
```

### Fix Applied
**File:** `app.py` (Lines 75-79)

```python
with app.app_context():
    # FIX: Create instance directory if it doesn't exist
    # SQLite requires the parent directory to exist before creating the database file
    # This prevents sqlite3.OperationalError: unable to open database file
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    os.makedirs(instance_path, exist_ok=True)
```

### What Changed
- Automatically creates the `instance/` directory if it doesn't exist
- Uses `exist_ok=True` to prevent errors if directory already exists
- Runs once on application startup

---

## 4. Relative Import Error

### Error
```
ImportError: attempted relative import with no known parent package
```

### Fix Applied
**File:** `main.py` (Lines 1-4)

```python
# FIX: Changed from relative import (from ..app import app) to absolute import (from app import app)
# Relative imports don't work when running main.py directly as a script
# This prevents ImportError: attempted relative import with no known parent package
from app import app
import routes  # noqa: F401
```

### What Changed
- Changed `from ..app import app` to `from app import app`
- Relative imports require the module to be part of a package
- Absolute imports work when running main.py directly as a script

---

## 5. Missing email_validator Package

### Error
```
ModuleNotFoundError: No module named 'email_validator'
Exception: Install 'email_validator' for email validation support.
```

### Fix Applied
**Command:**
```powershell
pip install email_validator
```

### What Changed
- Installed the required email_validator package for WTForms email field validation

---

## 6. Gmail Authentication Setup (Rolled Back)

### Note
Gmail OAuth authentication was attempted but rolled back because:
1. Flask-Dance blueprint was not initialized in app.py
2. Database schema changes caused compatibility issues
3. Gmail credentials environment variables were not set

### To Enable Gmail Authentication in Future:
1. Create Google OAuth credentials at: https://console.cloud.google.com/
2. Set environment variables:
   ```powershell
   $env:GOOGLE_OAUTH_CLIENT_ID = "your-client-id.apps.googleusercontent.com"
   $env:GOOGLE_OAUTH_CLIENT_SECRET = "your-client-secret"
   ```
3. Initialize Flask-Dance in app.py with proper configuration
4. Add migration to handle database schema changes

---

## Summary of All Files Modified

### app.py
- ✅ Fixed SESSION_SECRET with fallback
- ✅ Fixed DATABASE_URL with fallback and absolute path
- ✅ Added instance directory creation
- ✅ Added comprehensive comments

### main.py
- ✅ Fixed relative import to absolute import
- ✅ Added comprehensive comments

### models.py
- ✅ Added comprehensive comments explaining User model

### templates/login.html
- ✅ Removed Gmail login button (not fully implemented)

---

## Testing the Fixes

### Start the Application
```powershell
cd C:\Users\Tony\Group_Project_IB\EduDash
python .\main.py
```

### Expected Output
```
INFO:root:Database tables created
 * Serving Flask app 'app'
 * Debug mode: on
INFO:werkzeug:WARNING: This is a development server. Do not use it in a production deployment.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.2.104:5000
INFO:werkzeug:Press CTRL+C to quit
```

### Access the Application
- Open browser: http://localhost:5000
- Login with demo credentials:
  - **Student:** demo_student / password123
  - **Teacher:** demo_teacher / password123

---

## Production Deployment Checklist

- [ ] Set `SESSION_SECRET` environment variable to a secure random key
- [ ] Set `DATABASE_URL` environment variable (if not using SQLite)
- [ ] Disable debug mode: `debug=False` in main.py
- [ ] Use production WSGI server (Gunicorn, uWSGI, etc.)
- [ ] Enable HTTPS/SSL
- [ ] Set up proper logging
- [ ] Configure allowed hosts
- [ ] Set up database backups
- [ ] Configure email settings for notifications

---

## Environment Variables Reference

### Development
```powershell
# Optional - uses defaults if not set
$env:SESSION_SECRET = "dev-key"
$env:DATABASE_URL = "sqlite:///instance/edudash.db"
```

### Production
```powershell
# Required
$env:SESSION_SECRET = "secure-random-key-min-32-chars"
$env:DATABASE_URL = "postgresql://user:pass@host:5432/edudash"
```

---

## Support & Troubleshooting

### Issue: Database file not found
**Solution:** Delete `instance/edudash.db` and restart - it will be recreated

### Issue: Port 5000 already in use
**Solution:** Modify port in main.py or kill process using port 5000

### Issue: Module import errors
**Solution:** Ensure virtual environment is activated and all packages installed:
```powershell
pip install -r requirements.txt
```

---

**Last Updated:** November 14, 2025
**Application Status:** ✅ Fully Functional
