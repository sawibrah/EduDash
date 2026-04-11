# EduDash - Quick Start Guide

**Contributors:** for blueprints, pytest, Babel, and optional WeasyPrint / Google OAuth, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

**Roles (student / teacher / admin):** see [docs/USERS_AND_ROLES.md](docs/USERS_AND_ROLES.md).

## All Fixes Have Been Applied ✅

The EduDash application has been fixed and is ready to run. All startup errors have been resolved.

---

## Quick Start

### 1. Navigate to Project Directory
```powershell
cd C:\Users\Tony\Group_Project_IB\EduDash
```

### 2. Activate Virtual Environment
```powershell
.\myenv\Scripts\Activate.ps1
```

### 3. Run the Application
```powershell
python .\main.py
```

### 4. Access the Application
Open your browser and go to: **http://localhost:5000**

---

## Demo Credentials

These accounts are **not created automatically**. After a fresh clone or new database, run once from the project root:

```powershell
python scripts\seed_demo_users.py
```

Then you can sign in:

### Student Account
- **Username:** demo_student
- **Password:** password123

### Teacher Account
- **Username:** demo_teacher
- **Password:** password123

---

## What Was Fixed

| Error | Root Cause | Solution | Status |
|-------|-----------|----------|--------|
| SESSION_SECRET not set | Missing environment variable | Added fallback default | ✅ Fixed |
| DATABASE_URL not set | Missing environment variable | Added SQLite fallback | ✅ Fixed |
| Database file not found | Missing parent directory | Auto-create instance/ | ✅ Fixed |
| Import error | Relative imports | Changed to absolute import | ✅ Fixed |
| email_validator missing | Missing package | Installed package | ✅ Fixed |
| Gmail button broken | OAuth not initialized | Removed button (planned) | ✅ Fixed |

---

## File Changes Summary

### Modified Files
1. **app.py** - Added environment variable fallbacks with comments
2. **main.py** - Fixed import statement with comments
3. **models.py** - Added descriptive comments
4. **templates/login.html** - Removed broken Gmail button with notes

### New Files Created
1. **FIXES_SUMMARY.md** - Detailed explanation of all fixes
2. **QUICK_START.md** - This file

---

## Troubleshooting

### Port 5000 in Use
```powershell
# Find process using port 5000
Get-NetTCPConnection -LocalPort 5000 | Select-Object OwningProcess
# Kill the process
Stop-Process -Id <PID> -Force
```

### Database Issues
```powershell
# Delete database and restart (creates fresh database)
Remove-Item -Path instance\edudash.db -Force
python .\main.py
```

### Virtual Environment Issues
```powershell
# Deactivate current environment
deactivate
# Reactivate virtual environment
.\myenv\Scripts\Activate.ps1
```

---

## Production Deployment

### Set Environment Variables
```powershell
$env:SESSION_SECRET = "your-secure-random-key-min-32-chars"
$env:DATABASE_URL = "postgresql://user:password@host:5432/edudash"
```

### Run with Production Server
```powershell
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

---

## Features Status

- ✅ User Authentication (Login/Register)
- ✅ Role-Based Access (Student/Teacher/Admin)
- ✅ Course Management
- ✅ Quiz System
- ✅ Exam Management
- ✅ Multi-Language Support (English/French)
- ⏳ Gmail Authentication (Planned - see FIXES_SUMMARY.md)

---

## Contact & Support

For issues or questions, refer to:
- **FIXES_SUMMARY.md** - Detailed technical documentation
- **README.md** - General project information
- **ibra_readme.md** - Project-specific notes

---

**Status:** Application is fully functional and ready for development/testing
**Last Updated:** November 14, 2025
