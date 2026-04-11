"""
Create demo_student and demo_teacher (password: password123) if they do not exist.

Run from repository root:
    python scripts/seed_demo_users.py

Documentation mentions these accounts, but the app does not create them automatically.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import app, db  # noqa: E402
from models import StudentProfile, TeacherProfile, User  # noqa: E402

DEMO_PASSWORD = "password123"


def _ensure_demo_student() -> None:
    if User.query.filter_by(username="demo_student").first():
        print("demo_student: already exists — skipped")
        return
    u = User(
        username="demo_student",
        email="demo_student@example.com",
        first_name="Demo",
        last_name="Student",
        role="student",
    )
    u.set_password(DEMO_PASSWORD)
    db.session.add(u)
    db.session.flush()
    db.session.add(
        StudentProfile(
            user_id=u.id,
            student_id=f"STU{u.id:08d}",
            grade_level="9th Grade",
        )
    )
    db.session.commit()
    print("demo_student: created (password: password123)")


def _ensure_demo_teacher() -> None:
    if User.query.filter_by(username="demo_teacher").first():
        print("demo_teacher: already exists — skipped")
        return
    u = User(
        username="demo_teacher",
        email="demo_teacher@example.com",
        first_name="Demo",
        last_name="Teacher",
        role="teacher",
    )
    u.set_password(DEMO_PASSWORD)
    db.session.add(u)
    db.session.flush()
    db.session.add(
        TeacherProfile(
            user_id=u.id,
            employee_id=f"EMP{u.id:08d}",
            department="Computer Science",
        )
    )
    db.session.commit()
    print("demo_teacher: created (password: password123)")


def main() -> None:
    with app.app_context():
        db.create_all()
        _ensure_demo_student()
        _ensure_demo_teacher()


if __name__ == "__main__":
    main()
