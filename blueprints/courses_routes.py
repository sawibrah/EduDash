"""Shared course asset routes (slides, downloads) for teachers and students."""
import os

from flask import Blueprint, flash, redirect, render_template, send_file, url_for
from flask_babel import gettext
from flask_login import current_user

from auth import require_login
from blueprints.utils import convert_markdown_to_slides
from models import Course, Enrollment

courses_bp = Blueprint("courses", __name__)


@courses_bp.route("/course/<int:course_id>/download-slides")
@require_login
def download_course_slides(course_id):
    if current_user.is_teacher():
        course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    elif current_user.is_student():
        enrollment = Enrollment.query.filter_by(course_id=course_id, student_id=current_user.id).first()
        if not enrollment:
            flash(gettext("You are not enrolled in this course."), "error")
            return redirect(url_for("student.student_dashboard"))
        course = Course.query.get_or_404(course_id)
    else:
        flash(gettext("Access denied."), "error")
        return redirect(url_for("main.index"))
    if not course.uploaded_file_path or not os.path.exists(course.uploaded_file_path):
        flash(gettext("No slide file available for this course."), "error")
        if current_user.is_teacher():
            return redirect(url_for("teacher.view_course", course_id=course.id))
        return redirect(url_for("student.student_dashboard"))
    return send_file(course.uploaded_file_path, as_attachment=True, download_name=course.uploaded_file_name)


@courses_bp.route("/course/<int:course_id>/view-file")
@require_login
def view_course_file(course_id):
    if current_user.is_teacher():
        course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    elif current_user.is_student():
        enrollment = Enrollment.query.filter_by(course_id=course_id, student_id=current_user.id).first()
        if not enrollment:
            flash(gettext("You are not enrolled in this course."), "error")
            return redirect(url_for("student.student_dashboard"))
        course = Course.query.get_or_404(course_id)
    else:
        flash(gettext("Access denied."), "error")
        return redirect(url_for("main.index"))
    if not course.uploaded_file_path or not os.path.exists(course.uploaded_file_path):
        flash(gettext("No slide file available for this course."), "error")
        if current_user.is_teacher():
            return redirect(url_for("teacher.view_course", course_id=course.id))
        return redirect(url_for("student.student_dashboard"))
    return send_file(course.uploaded_file_path, as_attachment=False)


@courses_bp.route("/course/<int:course_id>/slides")
@require_login
def view_course_slides(course_id):
    if current_user.is_teacher():
        course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    elif current_user.is_student():
        enrollment = Enrollment.query.filter_by(course_id=course_id, student_id=current_user.id).first()
        if not enrollment:
            flash(gettext("You are not enrolled in this course."), "error")
            return redirect(url_for("student.student_dashboard"))
        course = Course.query.get_or_404(course_id)
    else:
        flash(gettext("Access denied."), "error")
        return redirect(url_for("main.index"))
    return render_template("course_slides.html", course=course)


@courses_bp.route("/course/<int:course_id>/slides/data")
def get_course_slides_data(course_id):
    course = Course.query.get_or_404(course_id)
    slides_content = convert_markdown_to_slides(course.content or "")
    return {
        "title": course.title,
        "content": slides_content,
        "programming_language": course.programming_language,
        "difficulty_level": course.difficulty_level,
    }
