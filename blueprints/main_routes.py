from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import current_user, login_user
from flask_babel import gettext
from app import app, db
from auth import require_login
from models import User, Course

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin.admin_dashboard"))
        if current_user.role == "student":
            return redirect(url_for("student.student_dashboard"))
        if current_user.role == "teacher":
            return redirect(url_for("teacher.teacher_dashboard"))
    return render_template("index.html")


@main_bp.route("/set_language/<language>")
def set_language(language=None):
    if language and language in app.config["LANGUAGES"]:
        session["language"] = language
    return redirect(request.referrer or url_for("main.index"))


@main_bp.route("/language")
def language():
    current_lang = session.get("language", app.config["BABEL_DEFAULT_LOCALE"])
    return jsonify({"current": current_lang, "available": list(app.config["LANGUAGES"].keys())})


@main_bp.route("/courses")
@require_login
def browse_courses():
    courses = Course.query.all()
    return render_template("browse_courses.html", courses=courses)


@main_bp.route("/test-login", methods=["GET", "POST"])
def test_login():
    if request.method == "POST":
        test_user = request.form.get("test_user")

        if test_user == "teacher":
            user = User.query.filter_by(username="teacher_test_001").first()
        elif test_user == "student":
            user = User.query.filter_by(username="student_test_001").first()
        else:
            flash(gettext("Invalid test user selected."), "error")
            return redirect(url_for("main.test_login"))

        if user:
            login_user(user)
            flash(
                gettext(
                    "Logged in as %(first)s %(last)s (%(role)s)",
                    first=user.first_name,
                    last=user.last_name,
                    role=user.role,
                ),
                "success",
            )
            if user.role == "student":
                return redirect(url_for("student.student_dashboard"))
            if user.role == "teacher":
                return redirect(url_for("teacher.teacher_dashboard"))
        else:
            flash(gettext("Test user not found."), "error")
            return redirect(url_for("main.test_login"))

    return render_template("test_login.html")
