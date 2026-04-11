"""Admin blueprint."""
from flask import Blueprint, redirect, render_template, request, url_for, flash
from flask_babel import gettext
from flask_login import current_user
from sqlalchemy.orm import joinedload

from app import db
from auth import require_role
from models import Course, Enrollment, Exam, Quiz, StudentProfile, TeacherProfile, User, CodeSubmission, ExamSubmission

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@require_role("admin")
def admin_dashboard():
    users = User.query.order_by(User.id.desc()).limit(10).all()
    total_users = User.query.count()
    total_students = User.query.filter_by(role="student").count()
    total_teachers = User.query.filter_by(role="teacher").count()
    total_admins = User.query.filter_by(role="admin").count()
    total_courses = Course.query.count()
    total_exams = Exam.query.count()
    total_quizzes = Quiz.query.count()
    total_enrollments = Enrollment.query.count()
    total_exam_submissions = ExamSubmission.query.count()
    total_quiz_submissions = CodeSubmission.query.count()
    recent_courses = Course.query.order_by(Course.created_at.desc()).limit(5).all()
    recent_enrollments = (
        Enrollment.query.options(joinedload(Enrollment.student), joinedload(Enrollment.course))
        .order_by(Enrollment.enrollment_date.desc())
        .limit(5)
        .all()
    )
    active_courses = Course.query.filter_by(course_status="published").count()
    return render_template(
        "admin_dashboard.html",
        users=users,
        total_users=total_users,
        total_students=total_students,
        total_teachers=total_teachers,
        total_admins=total_admins,
        total_courses=total_courses,
        total_exams=total_exams,
        total_quizzes=total_quizzes,
        total_enrollments=total_enrollments,
        total_exam_submissions=total_exam_submissions,
        total_quiz_submissions=total_quiz_submissions,
        recent_courses=recent_courses,
        recent_enrollments=recent_enrollments,
        active_courses=active_courses,
    )


@admin_bp.route("/users")
@require_role("admin")
def admin_users():
    users = (
        User.query.options(joinedload(User.teacher_profile), joinedload(User.student_profile))
        .order_by(User.created_at.desc())
        .all()
    )
    return render_template("admin_users.html", users=users)


@admin_bp.route("/courses")
@require_role("admin")
def admin_courses():
    courses = Course.query.options(joinedload(Course.teacher)).order_by(Course.created_at.desc()).all()
    return render_template("admin_courses.html", courses=courses)


@admin_bp.route("/user/<int:user_id>/promote", methods=["POST"])
@require_role("admin")
def promote_user(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get("new_role")
    if new_role not in ["student", "teacher", "admin"]:
        flash(gettext("Invalid role specified."), "error")
        return redirect(request.referrer or url_for("admin.admin_dashboard"))
    old_role = user.role
    user.role = new_role
    if new_role == "teacher":
        existing_teacher_profile = TeacherProfile.query.filter_by(user_id=user.id).first()
        if not existing_teacher_profile:
            teacher_profile = TeacherProfile()
            teacher_profile.user_id = user.id
            teacher_profile.employee_id = f"EMP{str(user.id).zfill(8)}"
            teacher_profile.department = "General"
            db.session.add(teacher_profile)
    db.session.commit()
    flash(
        gettext(
            "User %(username)s promoted from %(old_role)s to %(new_role)s successfully!",
            username=user.username,
            old_role=old_role,
            new_role=new_role,
        ),
        "success",
    )
    return redirect(request.referrer or url_for("admin.admin_dashboard"))


@admin_bp.route("/user/<int:user_id>/reset-password", methods=["POST"])
@require_role("admin")
def admin_reset_password(user_id):
    user = User.query.get_or_404(user_id)
    new_password = request.form.get("new_password")
    if not new_password or len(new_password) < 6:
        flash(gettext("Password must be at least 6 characters long."), "error")
        return redirect(request.referrer or url_for("admin.admin_users"))
    user.set_password(new_password)
    user.password_change_required = True
    db.session.commit()
    flash(
        gettext(
            "Password reset successfully for %(username)s. New password: %(new_password)s. User must change password on next login.",
            username=user.username,
            new_password=new_password,
        ),
        "success",
    )
    return redirect(request.referrer or url_for("admin.admin_users"))


@admin_bp.route("/user/create", methods=["POST"])
@require_role("admin")
def admin_create_user():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    role = request.form.get("role", "student")
    if not all([username, email, password, first_name, last_name]):
        flash(gettext("All fields are required."), "error")
        return redirect(url_for("admin.admin_users"))
    if len(password) < 6:
        flash(gettext("Password must be at least 6 characters long."), "error")
        return redirect(url_for("admin.admin_users"))
    if User.query.filter_by(username=username).first():
        flash(gettext("Username already exists."), "error")
        return redirect(url_for("admin.admin_users"))
    if User.query.filter_by(email=email).first():
        flash(gettext("Email already exists."), "error")
        return redirect(url_for("admin.admin_users"))
    new_user = User()
    new_user.username = username
    new_user.email = email
    new_user.first_name = first_name
    new_user.last_name = last_name
    new_user.role = role
    new_user.set_password(password)
    new_user.password_change_required = True
    db.session.add(new_user)
    db.session.flush()
    if role == "student":
        student_profile = StudentProfile()
        student_profile.user_id = new_user.id
        student_profile.student_id = f"STU{str(new_user.id).zfill(8)}"
        student_profile.grade_level = "Not Specified"
        db.session.add(student_profile)
    elif role == "teacher":
        teacher_profile = TeacherProfile()
        teacher_profile.user_id = new_user.id
        teacher_profile.employee_id = f"EMP{str(new_user.id).zfill(8)}"
        teacher_profile.department = "General"
        db.session.add(teacher_profile)
    db.session.commit()
    flash(gettext("User %(username)s created successfully as %(role)s!", username=username, role=role), "success")
    return redirect(url_for("admin.admin_users"))


@admin_bp.route("/user/<int:user_id>/toggle-teacher-capability", methods=["POST"])
@require_role("admin")
def admin_toggle_teacher_capability(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != "admin":
        flash(gettext("Can only toggle teacher capability for admin users."), "error")
        return redirect(url_for("admin.admin_users"))
    teacher_profile = TeacherProfile.query.filter_by(user_id=user.id).first()
    if teacher_profile:
        db.session.delete(teacher_profile)
        db.session.commit()
        flash(gettext("Teacher access removed from %(username)s.", username=user.username), "success")
    else:
        teacher_profile = TeacherProfile()
        teacher_profile.user_id = user.id
        teacher_profile.employee_id = f"EMP{str(user.id).zfill(8)}"
        teacher_profile.department = "Administration"
        db.session.add(teacher_profile)
        db.session.commit()
        flash(
            gettext(
                "Teacher access granted to %(username)s. They can now create and manage courses.",
                username=user.username,
            ),
            "success",
        )
    return redirect(url_for("admin.admin_users"))


@admin_bp.route("/course/<int:course_id>/toggle-status", methods=["POST"])
@require_role("admin")
def admin_toggle_course_status(course_id):
    course = Course.query.get_or_404(course_id)
    if course.course_status == "published":
        course.course_status = "draft"
        message = gettext('Course "%(title)s" set to draft.', title=course.title)
    else:
        course.course_status = "published"
        message = gettext('Course "%(title)s" published.', title=course.title)
    db.session.commit()
    flash(message, "success")
    return redirect(url_for("admin.admin_courses"))


@admin_bp.route("/user/<int:user_id>/delete", methods=["POST"])
@require_role("admin")
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    try:
        Enrollment.query.filter_by(student_id=user.id).delete()
        student_profile = StudentProfile.query.filter_by(user_id=user.id).first()
        if student_profile:
            db.session.delete(student_profile)
        teacher_profile = TeacherProfile.query.filter_by(user_id=user.id).first()
        if teacher_profile:
            db.session.delete(teacher_profile)
        db.session.delete(user)
        db.session.commit()
        flash(gettext("User '%(username)s' deleted successfully!", username=user.username), "success")
    except Exception as e:
        db.session.rollback()
        flash(gettext("Error deleting user: %(err)s", err=str(e)), "error")
    return redirect(url_for("admin.admin_users"))
