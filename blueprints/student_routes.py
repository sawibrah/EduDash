"""Student-facing routes (dashboard, enrollment, exams, quizzes, student PDF)."""
import json
import os
from datetime import datetime

import markdown
from flask import Blueprint, flash, jsonify, redirect, render_template, request, send_file, url_for
from flask_babel import gettext
from flask_login import current_user
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

try:
    import weasyprint
except ImportError:
    weasyprint = None

from app import db
from auth import require_role
from models import CodeSubmission, Course, Enrollment, Exam, ExamSubmission, Quiz

student_bp = Blueprint("student", __name__)


@student_bp.route("/student/dashboard")
@require_role("student")
def student_dashboard():
    enrollments = Enrollment.query.options(
        joinedload(Enrollment.course).joinedload(Course.teacher)
    ).filter_by(student_id=current_user.id).all()
    enrolled_courses = [enrollment.course for enrollment in enrollments]
    course_ids = [course.id for course in enrolled_courses]
    exams = (
        Exam.query.options(joinedload(Exam.course)).filter(Exam.course_id.in_(course_ids), Exam.is_active == True).all()
        if course_ids
        else []
    )
    submitted_exam_ids = [s.exam_id for s in ExamSubmission.query.filter_by(student_id=current_user.id).all()]
    exams = [e for e in exams if e.id not in submitted_exam_ids]
    exams.sort(key=lambda x: x.due_date if x.due_date else datetime.max)
    quizzes = (
        Quiz.query.options(joinedload(Quiz.course))
        .filter(Quiz.course_id.in_(course_ids), Quiz.is_active == True)
        .all()
        if course_ids
        else []
    )
    submitted_quiz_ids = [s.quiz_id for s in CodeSubmission.query.filter_by(student_id=current_user.id).all()]
    quizzes = [q for q in quizzes if q.id not in submitted_quiz_ids]
    quizzes.sort(key=lambda x: x.due_date if x.due_date else datetime.max)
    return render_template(
        "student_dashboard.html",
        courses=enrolled_courses,
        exams=exams[:5],
        quizzes=quizzes[:5],
    )


@student_bp.route("/student/enroll", methods=["POST"])
@require_role("student")
def enroll_course():
    course_id = request.form.get("course_id")
    if not course_id:
        flash(gettext("Course ID is required."), "error")
        return redirect(url_for("student.student_dashboard"))
    try:
        cid = int(course_id)
    except (TypeError, ValueError):
        course = None
    else:
        course = db.session.get(Course, cid)
    if not course:
        flash(gettext("Course not found."), "error")
        return redirect(url_for("student.student_dashboard"))
    existing = Enrollment.query.filter_by(student_id=current_user.id, course_id=course_id).first()
    if existing:
        flash(gettext("You are already enrolled in this course."), "warning")
        return redirect(url_for("student.student_dashboard"))
    enrollment = Enrollment()
    enrollment.student_id = current_user.id
    enrollment.course_id = course_id
    db.session.add(enrollment)
    db.session.commit()
    flash(gettext("Successfully enrolled in %(title)s!", title=course.title), "success")
    return redirect(url_for("student.student_dashboard"))


@student_bp.route("/student/course/<int:course_id>/download-pdf")
@require_role("student")
def student_download_course_pdf(course_id):
    enrollment = Enrollment.query.filter_by(course_id=course_id, student_id=current_user.id).first()
    if not enrollment:
        flash(gettext("You are not enrolled in this course."), "error")
        return redirect(url_for("student.student_dashboard"))
    course = db.get_or_404(Course, course_id)
    if weasyprint is None:
        flash(
            gettext(
                "PDF export requires WeasyPrint. Install optional dependencies "
                "(see requirements-pdf.txt or project README)."
            ),
            "error",
        )
        return redirect(url_for("student.student_dashboard"))
    try:
        from flask import current_app

        pdf_dir = os.path.join(current_app.root_path, "static", "pdfs")
        os.makedirs(pdf_dir, exist_ok=True)
        content_html = markdown.markdown(
            course.content or "No content available.", extensions=["codehilite", "fenced_code"]
        )
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{course.title}</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                h2 {{ color: #34495e; margin-top: 30px; }}
                h3 {{ color: #7f8c8d; }}
                .course-info {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .course-info p {{ margin: 5px 0; }}
                code {{ background: #f1f2f6; padding: 2px 4px; border-radius: 3px; font-family: monospace; }}
                pre {{ background: #2f3640; color: #f1f2f6; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                pre code {{ background: none; padding: 0; }}
                .content {{ margin-top: 30px; }}
                @page {{ size: A4; margin: 2cm; }}
            </style>
        </head>
        <body>
            <h1>{course.title}</h1>
            <div class="course-info">
                <p><strong>Description:</strong> {course.description or 'No description provided'}</p>
                <p><strong>Programming Language:</strong> {course.programming_language or 'Not specified'}</p>
                <p><strong>Difficulty Level:</strong> {course.difficulty_level or 'Not specified'}</p>
                <p><strong>Estimated Hours:</strong> {course.estimated_hours or 'Not specified'}</p>
                <p><strong>Prerequisites:</strong> {course.prerequisites or 'None'}</p>
                <p><strong>Learning Objectives:</strong> {course.learning_objectives or 'Not specified'}</p>
            </div>
            <div class="content">
                <h2>Course Content</h2>
                {content_html}
            </div>
        </body>
        </html>
        """
        pdf_filename = f"course_{course_id}_{secure_filename(course.title)}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        weasyprint.HTML(string=html_content).write_pdf(pdf_path)
        return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)
    except Exception as e:
        flash(gettext("Error generating PDF: %(err)s", err=str(e)), "error")
        return redirect(url_for("student.student_dashboard"))


@student_bp.route("/student/exam/<int:exam_id>/take")
@require_role("student")
def student_take_exam(exam_id):
    exam = db.get_or_404(Exam, exam_id)
    enrollment = Enrollment.query.filter_by(student_id=current_user.id, course_id=exam.course_id).first()
    if not enrollment:
        flash(gettext("You must be enrolled in this course to take the exam."), "error")
        return redirect(url_for("student.student_dashboard"))
    if not exam.is_active:
        flash(gettext("This exam is not currently active."), "warning")
        return redirect(url_for("student.student_dashboard"))
    existing_submission = ExamSubmission.query.filter_by(exam_id=exam_id, student_id=current_user.id).first()
    if existing_submission:
        flash(gettext("You have already submitted this exam."), "info")
        return redirect(url_for("student.student_dashboard"))
    course = db.session.get(Course, exam.course_id)
    return render_template("student_take_exam.html", exam=exam, course=course)


@student_bp.route("/student/exam/<int:exam_id>/submit", methods=["POST"])
@require_role("student")
def student_submit_exam(exam_id):
    exam = db.get_or_404(Exam, exam_id)
    enrollment = Enrollment.query.filter_by(student_id=current_user.id, course_id=exam.course_id).first()
    if not enrollment:
        return jsonify({"success": False, "message": gettext("Not enrolled in this course")}), 403
    existing_submission = ExamSubmission.query.filter_by(exam_id=exam_id, student_id=current_user.id).first()
    if existing_submission:
        return jsonify({"success": False, "message": gettext("Already submitted")}), 400
    data = request.get_json() if request.is_json else None
    if not data:
        return jsonify({"success": False, "message": gettext("No data provided")}), 400
    answers = data.get("answers", {})
    questions = json.loads(exam.questions_json) if exam.questions_json else []
    score = 0
    total_questions = len(questions)
    for idx, question in enumerate(questions):
        student_answer = answers.get(str(idx))
        correct_answer = question.get("correct_answer", 0)
        if student_answer is not None and int(student_answer) == int(correct_answer):
            score += 1
    percentage_score = int((score / total_questions * exam.max_score)) if total_questions > 0 else 0
    submission = ExamSubmission()
    submission.exam_id = exam_id
    submission.student_id = current_user.id
    submission.answers_json = json.dumps(answers)
    submission.score = percentage_score
    submission.status = "graded"
    submission.submitted_at = datetime.now()
    submission.graded_at = datetime.now()
    db.session.add(submission)
    db.session.commit()
    return jsonify(
        {
            "success": True,
            "score": percentage_score,
            "total": exam.max_score,
            "message": gettext(
                "Exam submitted successfully! You scored %(score)s/%(total)s",
                score=percentage_score,
                total=exam.max_score,
            ),
        }
    )


@student_bp.route("/quiz/<int:quiz_id>")
@require_role("student")
def take_quiz(quiz_id):
    quiz = db.get_or_404(Quiz, quiz_id)
    enrollment = Enrollment.query.filter_by(student_id=current_user.id, course_id=quiz.course_id).first()
    if not enrollment:
        flash(gettext("You are not enrolled in this course."), "error")
        return redirect(url_for("student.student_dashboard"))
    if not quiz.is_active:
        flash(gettext("This quiz is not currently active."), "error")
        return redirect(url_for("student.student_dashboard"))
    if quiz.due_date and datetime.now() > quiz.due_date:
        flash(gettext("This quiz is past its due date."), "error")
        return redirect(url_for("student.student_dashboard"))
    existing_submission = CodeSubmission.query.filter_by(quiz_id=quiz_id, student_id=current_user.id).first()
    if existing_submission:
        return render_template("student_quiz_submitted.html", quiz=quiz, submission=existing_submission)
    return render_template("student_take_mcq_quiz.html", quiz=quiz)


@student_bp.route("/quiz/<int:quiz_id>/submit", methods=["POST"])
@require_role("student")
def submit_quiz(quiz_id):
    quiz = db.get_or_404(Quiz, quiz_id)
    enrollment = Enrollment.query.filter_by(student_id=current_user.id, course_id=quiz.course_id).first()
    if not enrollment:
        return jsonify({"success": False, "error": gettext("Not enrolled in course")})
    existing_submission = CodeSubmission.query.filter_by(quiz_id=quiz_id, student_id=current_user.id).first()
    if existing_submission:
        return jsonify({"success": False, "error": gettext("Already submitted")})
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": gettext("No data provided")})
    submission = CodeSubmission()
    submission.quiz_id = quiz_id
    submission.student_id = current_user.id
    submission.submitted_at = datetime.now()
    answers = data.get("answers", {})
    submission.answers_json = json.dumps(answers)
    submission.code_content = ""
    questions = json.loads(quiz.questions_json or "[]")
    correct_count = 0
    total_questions = len(questions)
    for idx, question in enumerate(questions):
        student_answer = answers.get(str(idx))
        correct_answer = question.get("correct_answer")
        if isinstance(correct_answer, str) and len(correct_answer) == 1:
            correct_answer_idx = ord(correct_answer.upper()) - ord("A")
        else:
            correct_answer_idx = correct_answer
        if student_answer is not None and student_answer == correct_answer_idx:
            correct_count += 1
    if total_questions > 0:
        submission.score = int((correct_count / total_questions) * quiz.max_score)
    else:
        submission.score = 0
    submission.status = "graded"
    submission.graded_at = datetime.now()
    db.session.add(submission)
    db.session.commit()
    return jsonify({"success": True, "message": gettext("Quiz submitted successfully"), "score": submission.score})
