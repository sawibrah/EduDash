# -*- coding: utf-8 -*-
"""Build blueprint modules from routes.py (run: python scripts/_build_blueprints_from_routes.py)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
routes = (ROOT / "routes.py").read_text(encoding="utf-8")
lines = routes.splitlines(keepends=True)


def slice_lines(start: int, end: int) -> str:
    return "".join(lines[start - 1 : end])


def teacher_body() -> str:
    parts = [
        slice_lines(594, 807),
        slice_lines(861, 937),
        slice_lines(1089, 1210),
        slice_lines(1346, 1443),
        slice_lines(1510, 1806),
    ]
    body = "".join(parts)
    body = body.replace("from app import app, db, csrf", "")
    body = body.replace("@app.route('/teacher/", "@teacher_bp.route('/")
    body = body.replace("@app.route(\"/teacher/", "@teacher_bp.route(\"/")
    body = body.replace("app.instance_path", "current_app.instance_path")
    body = body.replace("app.root_path", "current_app.root_path")
    # url_for in teacher file: prefix teacher.
    import re

    def uf(m):
        name = m.group(1)
        if name == "static":
            return m.group(0)
        if name in (
            "student_dashboard",
            "student_take_exam",
            "student_download_course_pdf",
            "enroll_course",
            "take_quiz",
            "submit_quiz",
            "index",
            "set_language",
            "language",
            "browse_courses",
            "test_login",
            "login",
            "logout",
            "register",
            "change_password",
            "admin_dashboard",
            "admin_users",
            "admin_courses",
            "promote_user",
            "admin_reset_password",
            "admin_create_user",
            "admin_toggle_teacher_capability",
            "admin_toggle_course_status",
            "admin_delete_user",
            "available_courses_api",
            "download_course_slides",
            "view_course_file",
            "view_course_slides",
            "get_course_slides_data",
        ):
            bp = {
                "student_dashboard": "student",
                "student_take_exam": "student",
                "student_download_course_pdf": "student",
                "enroll_course": "student",
                "take_quiz": "quiz",
                "submit_quiz": "quiz",
                "index": "main",
                "set_language": "main",
                "language": "main",
                "browse_courses": "main",
                "test_login": "main",
                "login": "auth",
                "logout": "auth",
                "register": "auth",
                "change_password": "auth",
                "admin_dashboard": "admin",
                "admin_users": "admin",
                "admin_courses": "admin",
                "promote_user": "admin",
                "admin_reset_password": "admin",
                "admin_create_user": "admin",
                "admin_toggle_teacher_capability": "admin",
                "admin_toggle_course_status": "admin",
                "admin_delete_user": "admin",
                "available_courses_api": "api",
                "download_course_slides": "courses",
                "view_course_file": "courses",
                "view_course_slides": "courses",
                "get_course_slides_data": "courses",
            }.get(name, "teacher")
            return f"url_for('{bp}.{name}'"
        return f"url_for('teacher.{name}'"

    body = re.sub(r"url_for\('([^']+)'", uf, body)
    body = body.replace("url_for('teacher.teacher.", "url_for('teacher.")
    return body


HEADER = '''"""Teacher blueprint (courses, exams, quizzes, PDF)."""
import json
import os
from datetime import datetime

import bleach
import markdown
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_babel import gettext
from flask_login import current_user
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

try:
    import weasyprint
except ImportError:
    weasyprint = None

from app import db, csrf
from auth import require_role
from blueprints.utils import UPLOAD_FOLDER, allowed_file, generate_5_slide_template
from models import CodeSubmission, Course, Enrollment, Exam, ExamSubmission, Quiz, User

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")

'''

FOOTER = "\n"


def main():
    out = HEADER + teacher_body() + FOOTER
    (ROOT / "blueprints" / "teacher_routes.py").write_text(out, encoding="utf-8")
    print("Wrote blueprints/teacher_routes.py", len(out), "bytes")


if __name__ == "__main__":
    main()
