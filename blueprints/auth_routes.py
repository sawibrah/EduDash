from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_user, logout_user
from flask_babel import gettext
from app import db
from auth import require_login
from forms import RegistrationForm, LoginForm
from models import User, StudentProfile

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role="student",
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        student_profile = StudentProfile(
            user_id=user.id,
            student_id=f"STU{user.id:08d}",
            grade_level=form.grade_level.data if form.grade_level.data else "9th Grade",
        )
        db.session.add(student_profile)
        db.session.commit()
        flash(gettext("Registration successful! Welcome, %(name)s!", name=user.first_name), "success")
        login_user(user)
        return redirect(url_for("student.student_dashboard"))

    return render_template("register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            if user.password_change_required:
                flash(gettext("You must change your password before continuing."), "warning")
                return redirect(url_for("auth.change_password"))

            next_page = request.args.get("next")
            flash(gettext("Welcome back, %(name)s!", name=user.first_name), "success")

            if next_page:
                return redirect(next_page)
            if user.role == "admin":
                return redirect(url_for("admin.admin_dashboard"))
            if user.role == "student":
                return redirect(url_for("student.student_dashboard"))
            return redirect(url_for("teacher.teacher_dashboard"))
        flash(gettext("Invalid username or password."), "error")

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@require_login
def logout():
    user_name = current_user.first_name
    logout_user()
    flash(gettext("You have been logged out, %(name)s. See you next time!", name=user_name), "info")
    return redirect(url_for("main.index"))


@auth_bp.route("/change-password", methods=["GET", "POST"])
@require_login
def change_password():
    from forms import ChangePasswordForm

    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash(gettext("Current password is incorrect."), "error")
            return render_template(
                "change_password.html", form=form, required=current_user.password_change_required
            )

        current_user.set_password(form.new_password.data)
        current_user.password_change_required = False
        db.session.commit()
        flash(gettext("Password changed successfully!"), "success")

        if current_user.role == "admin":
            return redirect(url_for("admin.admin_dashboard"))
        if current_user.role == "student":
            return redirect(url_for("student.student_dashboard"))
        return redirect(url_for("teacher.teacher_dashboard"))

    return render_template(
        "change_password.html", form=form, required=current_user.password_change_required
    )
