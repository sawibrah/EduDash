# Users, roles, and permissions

EduPortal uses **three primary roles**: **student**, **teacher**, and **admin**. After sign-in, each user is sent to the dashboard that matches their role.

---

## Sign-in and registration

- **Register** (`/register`): new accounts are **students** by default. A student profile is created automatically.
- **Login** (`/login`): email/username + password. If an admin has forced a password reset, the user is redirected to **change password** first.
- **Logout** (`/logout`): ends the session.

**Demo accounts** (optional local testing):

| Role    | Username       | Password     |
|---------|----------------|--------------|
| Student | `demo_student` | `password123` |
| Teacher | `demo_teacher` | `password123` |

They are **not** inserted by the app on startup. To create them (and fix “Invalid username or password” for demos), run from the repo root:

```powershell
python scripts/seed_demo_users.py
```

Otherwise use **Register** (student) or ask an **admin** to create users.

---

## Student

**Typical home:** **Student dashboard** (`/student/dashboard`).

**What students can do**

- See **courses they are enrolled in**, upcoming **exams** and **quizzes**, and quick actions (slides, downloads where available).
- **Enroll** in published courses (from the dashboard / browse flow).
- **View course slides** and related materials for enrolled courses (`/course/...` routes).
- **Take exams** (`/student/exam/<id>/take`) and **submit** answers (auto-graded MCQ where configured).
- **Take quizzes** (`/quiz/<id>`) and submit responses.
- **Download a course PDF** (when WeasyPrint is installed on the server; otherwise a message explains that PDF export is optional).

**Restrictions**

- Cannot create or edit courses, exams, or quizzes.
- Cannot open teacher-only URLs (e.g. `/teacher/...` for someone else’s course).

---

## Teacher

**Typical home:** **Teacher dashboard** (`/teacher/dashboard`).

**What teachers can do**

- **Create and edit courses** (markdown, uploads, metadata, draft vs published where applicable).
- **Manage students** enrolled in their courses (view roster, remove enrollment where the UI allows it).
- **Create and manage exams** (MCQ, due dates, activate/deactivate, edit, delete).
- **Create and manage quizzes** (including MCQ-style flows in the app).
- **Open course slides** for **their own** courses (preview same content students use).
- **Generate / download course PDFs** when optional PDF dependencies are installed.

**Restrictions**

- Course and assessment actions apply only to **courses they own** (`teacher_id` matches their user id).
- Cannot use **admin-only** pages unless they also have the **admin** role (see below).

---

## Admin

**Typical home:** **Admin dashboard** (`/admin/dashboard`).

**What admins can do**

- View **high-level statistics** (users, courses, enrollments, submissions, etc.).
- **User management** (`/admin/users`): list users, **create** users, **change roles** (student / teacher / admin), **reset passwords** (user must change password on next login if you use that flow), **delete** users (with care), and for **admin** accounts only: **grant or remove “teacher capability”** (extra teacher profile so an admin can also use teacher tools).

- **Course oversight** (`/admin/courses`): view all courses; **publish** or set to **draft** platform-wide.

**Restrictions**

- Admins follow the same **login** and **password change** rules as other users.
- **Teacher-only** routes still require either role `teacher` **or** admin **with** teacher capability (see `auth.require_role` in the codebase). A plain admin without teacher profile cannot manage another teacher’s course content as a “teacher” until teacher access is granted.

---

## Role summary table

| Capability | Student | Teacher | Admin |
|------------|:-------:|:-------:|:-----:|
| Own student dashboard | ✓ | — | — |
| Own teacher dashboard | — | ✓ | —* |
| Own admin dashboard | — | — | ✓ |
| Enroll in published courses | ✓ | — | —* |
| Create / edit own courses & assessments | — | ✓ | —* |
| Manage all users & global course status | — | — | ✓ |

\*Admin with **teacher capability** can also use teacher features like a teacher.

---

## Creating the first administrator

There is no public “register as admin” flow. The **first admin** is usually created **once** in a Python shell (or a secure internal script), with a **strong password** you change immediately after login.

Example pattern (adjust email/password; run inside `with app.app_context():`):

```python
from app import app, db
from models import User

with app.app_context():
    if User.query.filter_by(username="admin").first():
        print("Admin already exists")
    else:
        u = User(
            username="admin",
            email="admin@yourdomain.example",
            first_name="Admin",
            last_name="User",
            role="admin",
        )
        u.set_password("REPLACE_WITH_STRONG_PASSWORD")
        db.session.add(u)
        db.session.commit()
```

Never commit real passwords or personal emails into the repository.

---

## Related docs

- [QUICK_START.md](../QUICK_START.md) — run the app, demo logins, troubleshooting  
- [docs/DEVELOPMENT.md](DEVELOPMENT.md) — developers: blueprints, tests, i18n  
