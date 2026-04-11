"""Teacher blueprint (courses, exams, quizzes, PDF)."""
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

from app import db
from auth import require_role
from blueprints.utils import UPLOAD_FOLDER, allowed_file, generate_5_slide_template
from models import CodeSubmission, Course, Enrollment, Exam, ExamSubmission, Quiz, User

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")

@teacher_bp.route('/create-course', methods=['GET', 'POST'])
@require_role('teacher')
def create_course():
    if request.method == 'POST':
        # Check if user wants to use the 5-slide template
        use_template = request.form.get('use_5_slide_template')
        
        if use_template == '1':
            title = request.form.get('title', '')
            programming_language = request.form.get('programming_language', '')
            template_content = generate_5_slide_template(title, programming_language)
            
            # Return the form with the template pre-filled
            return render_template('teacher_create_course.html', 
                                 template_content=template_content,
                                 title=title,
                                 programming_language=programming_language,
                                 use_template=True)
        title = request.form.get('title')
        description = request.form.get('description')
        content = request.form.get('content', '')
        difficulty_level = request.form.get('difficulty_level')
        programming_language = request.form.get('programming_language')
        estimated_hours = request.form.get('estimated_hours')
        prerequisites = request.form.get('prerequisites', '')
        learning_objectives = request.form.get('learning_objectives', '')
        course_status = request.form.get('course_status', 'draft')
        
        if not title:
            flash(gettext('Course title is required.'), 'error')
            return render_template('teacher_create_course.html')
        
        course = Course()
        course.title = title
        course.description = description
        course.content = content
        course.difficulty_level = difficulty_level
        course.programming_language = programming_language
        course.estimated_hours = int(estimated_hours) if estimated_hours and estimated_hours.strip() else None
        course.prerequisites = prerequisites
        course.learning_objectives = learning_objectives
        course.course_status = course_status
        course.content_display_type = request.form.get('content_display_type', 'markdown')
        course.teacher_id = current_user.id
        
        # Handle file upload
        if 'slide_file' in request.files:
            file = request.files['slide_file']
            if file and file.filename and allowed_file(file.filename):
                try:
                    # Create upload directory if it doesn't exist
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    
                    # Generate secure filename
                    filename = secure_filename(file.filename)
                    timestamp = int(datetime.now().timestamp())
                    file_extension = filename.rsplit('.', 1)[1].lower()
                    secure_name = f"course_{timestamp}_{filename}"
                    file_path = os.path.join(UPLOAD_FOLDER, secure_name)
                    
                    # Save file
                    file.save(file_path)
                    
                    # Update course with file info
                    course.uploaded_file_path = file_path
                    course.uploaded_file_type = file_extension
                    course.uploaded_file_name = filename
                    
                    flash(gettext('Course slide file "%(filename)s" uploaded successfully!', filename=filename), 'success')
                    
                except Exception as e:
                    flash(gettext('Error uploading file: %(err)s', err=str(e)), 'error')
        
        db.session.add(course)
        db.session.commit()
        
        flash(gettext('Programming course created successfully!'), 'success')
        return redirect(url_for('teacher.teacher_dashboard'))
    
    return render_template('teacher_create_course.html')

@teacher_bp.route('/course/<int:course_id>')
@require_role('teacher')
def view_course(course_id):
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    # Convert markdown to HTML for preview and sanitize to prevent XSS
    if course.content:
        content_html = markdown.markdown(course.content, extensions=['codehilite', 'fenced_code'])
        # Sanitize HTML while allowing safe tags for educational content
        allowed_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li', 
                       'code', 'pre', 'blockquote', 'a', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'div', 'span']
        allowed_attrs = {'a': ['href', 'title'], 'code': ['class'], 'pre': ['class'], 'div': ['class'], 'span': ['class']}
        content_html = bleach.clean(content_html, tags=allowed_tags, attributes=allowed_attrs, strip=True)
    else:
        content_html = ''
    return render_template('teacher_view_course.html', course=course, content_html=content_html)

@teacher_bp.route('/course/<int:course_id>/students')
@require_role('teacher')
def view_course_students(course_id):
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    # Eager load student relationships to avoid N+1 queries
    enrollments = Enrollment.query.options(
        joinedload(Enrollment.student)
    ).filter_by(course_id=course_id).all()
    return render_template('teacher_course_students.html', course=course, enrollments=enrollments)

@teacher_bp.route('/course/<int:course_id>/exams')
@require_role('teacher')
def view_course_exams(course_id):
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    exams = Exam.query.filter_by(course_id=course_id).order_by(Exam.created_at.desc()).all()
    return render_template('teacher_course_exams.html', course=course, exams=exams, now=datetime.now())

@teacher_bp.route('/course/<int:course_id>/create-exam')
@require_role('teacher')
def show_create_exam(course_id):
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    return render_template('teacher_create_exam.html', course=course)

@teacher_bp.route('/course/<int:course_id>/edit', methods=['GET', 'POST'])
@require_role('teacher')
def edit_course(course_id):
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        course.title = request.form.get('title')
        course.description = request.form.get('description')
        course.content = request.form.get('content', '')
        course.difficulty_level = request.form.get('difficulty_level')
        course.programming_language = request.form.get('programming_language')
        estimated_hours_str = request.form.get('estimated_hours')
        course.estimated_hours = int(estimated_hours_str) if estimated_hours_str and estimated_hours_str.strip() else None
        course.prerequisites = request.form.get('prerequisites', '')
        course.learning_objectives = request.form.get('learning_objectives', '')
        course.course_status = request.form.get('course_status', 'draft')
        course.content_display_type = request.form.get('content_display_type', 'markdown')
        course.updated_at = datetime.now()
        
        # Handle file upload
        if 'slide_file' in request.files:
            file = request.files['slide_file']
            if file and file.filename and allowed_file(file.filename):
                try:
                    # Remove old file if exists
                    if course.uploaded_file_path and os.path.exists(course.uploaded_file_path):
                        os.remove(course.uploaded_file_path)
                    
                    # Create upload directory if it doesn't exist
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    
                    # Generate secure filename
                    filename = secure_filename(file.filename)
                    timestamp = int(datetime.now().timestamp())
                    file_extension = filename.rsplit('.', 1)[1].lower()
                    secure_name = f"course_{course_id}_{timestamp}_{filename}"
                    file_path = os.path.join(UPLOAD_FOLDER, secure_name)
                    
                    # Save file
                    file.save(file_path)
                    
                    # Update course with file info
                    course.uploaded_file_path = file_path
                    course.uploaded_file_type = file_extension
                    course.uploaded_file_name = filename
                    
                    flash(gettext('Course slide file "%(filename)s" uploaded successfully!', filename=filename), 'success')
                    
                except Exception as e:
                    flash(gettext('Error uploading file: %(err)s', err=str(e)), 'error')
        
        db.session.commit()
        flash(gettext('Course updated successfully!'), 'success')
        return redirect(url_for('teacher.view_course', course_id=course.id))
    
    return render_template('teacher_edit_course.html', course=course)

@teacher_bp.route('/course/<int:course_id>/delete', methods=['POST'])
@require_role('teacher')
def delete_course(course_id):
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    
    try:
        # Delete associated uploaded files if they exist
        if course.uploaded_file_path and os.path.exists(course.uploaded_file_path):
            os.remove(course.uploaded_file_path)
        
        # Delete generated PDF if it exists
        if course.pdf_path and os.path.exists(course.pdf_path):
            os.remove(course.pdf_path)
        
        # Delete course exams first (due to foreign key constraints)
        exams = Exam.query.filter_by(course_id=course_id).all()
        for exam in exams:
            db.session.delete(exam)
        
        # Delete enrollments
        enrollments = Enrollment.query.filter_by(course_id=course_id).all()
        for enrollment in enrollments:
            db.session.delete(enrollment)
        
        # Finally delete the course
        course_title = course.title
        db.session.delete(course)
        db.session.commit()
        
        flash(gettext('Course "%(title)s" deleted successfully!', title=course_title), 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(gettext('Error deleting course: %(err)s', err=str(e)), 'error')
    
    return redirect(url_for('teacher.teacher_dashboard'))

@teacher_bp.route('/course/<int:course_id>/generate-pdf', methods=['POST'])
@require_role('teacher')
def generate_course_pdf(course_id):
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    if weasyprint is None:
        flash(
            gettext(
                "PDF generation requires WeasyPrint. Install optional dependencies "
                "(see requirements-pdf.txt or project README)."
            ),
            "error",
        )
        return redirect(url_for("teacher.view_course", course_id=course.id))
    try:
        # Create PDF directory if it doesn't exist
        pdf_dir = os.path.join(current_app.instance_path, 'pdfs')
        os.makedirs(pdf_dir, exist_ok=True)
        
        # Convert markdown content to HTML
        content_html = markdown.markdown(course.content or '', extensions=['codehilite', 'fenced_code'])
        
        # Create HTML template for PDF
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{course.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1, h2, h3 {{ color: #333; }}
                .course-info {{ background: #f5f5f5; padding: 20px; margin: 20px 0; }}
                .content {{ margin: 20px 0; }}
                pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; }}
                code {{ background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
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
        
        # Generate PDF
        pdf_filename = f"course_{course_id}_{secure_filename(course.title)}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        
        # Create PDF from HTML
        weasyprint.HTML(string=html_content).write_pdf(pdf_path)
        
        # Update course record
        course.pdf_generated = True
        course.pdf_path = pdf_path
        db.session.commit()
        
        flash(gettext('PDF generated successfully!'), 'success')
        return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)
        
    except Exception as e:
        flash(gettext('Error generating PDF: %(err)s', err=str(e)), 'error')
        return redirect(url_for('teacher.view_course', course_id=course.id))

@teacher_bp.route('/course/<int:course_id>/download-pdf')
@require_role('teacher')
def download_course_pdf(course_id):
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    
    if not course.pdf_generated or not course.pdf_path or not os.path.exists(course.pdf_path):
        flash(gettext('PDF not available. Please generate it first.'), 'error')
        return redirect(url_for('teacher.view_course', course_id=course.id))
    
    pdf_filename = f"course_{course_id}_{secure_filename(course.title)}.pdf"
    return send_file(course.pdf_path, as_attachment=True, download_name=pdf_filename)
@teacher_bp.route('/create-exam', methods=['POST'])
@require_role('teacher')
def create_exam():
    title = request.form.get('title')
    description = request.form.get('description')
    course_id = request.form.get('course_id')
    questions_json = request.form.get('questions_json')
    max_score = request.form.get('max_score', 100)
    time_limit = request.form.get('time_limit', 60)
    due_date_str = request.form.get('due_date')
    is_active = request.form.get('is_active') == 'on'
    
    if not title:
        flash(gettext('Exam title is required.'), 'error')
        return redirect(url_for('teacher.teacher_dashboard'))
    
    if not course_id:
        flash(gettext('Course ID is required.'), 'error')
        return redirect(url_for('teacher.teacher_dashboard'))
    
    # Verify teacher owns the course
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first()
    if not course:
        flash(gettext('Invalid course selected.'), 'error')
        return redirect(url_for('teacher.teacher_dashboard'))
    
    due_date = None
    if due_date_str:
        try:
            if 'T' in due_date_str:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            else:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        except ValueError:
            flash(gettext('Invalid due date format.'), 'error')
            return redirect(url_for('teacher.show_create_exam', course_id=course_id))
    
    exam = Exam()
    exam.title = title
    exam.description = description
    exam.course_id = course_id
    exam.questions_json = questions_json
    exam.max_score = int(max_score) if max_score else 100
    exam.time_limit = int(time_limit) if time_limit else 60
    exam.due_date = due_date
    exam.is_active = is_active
    db.session.add(exam)
    db.session.commit()
    
    flash(gettext('Exam created successfully!'), 'success')
    return redirect(url_for('teacher.view_course_exams', course_id=course_id))

@teacher_bp.route('/exam/<int:exam_id>/edit-mcq')
@require_role('teacher')
def show_edit_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    course = Course.query.filter_by(id=exam.course_id, teacher_id=current_user.id).first()
    
    if not course:
        flash(gettext('You do not have permission to edit this exam.'), 'error')
        return redirect(url_for('teacher.teacher_dashboard'))
    
    return render_template('teacher_edit_exam.html', exam=exam, course=course)

@teacher_bp.route('/exam/<int:exam_id>/update', methods=['POST'])
@require_role('teacher')
def update_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    course = Course.query.filter_by(id=exam.course_id, teacher_id=current_user.id).first()
    
    if not course:
        flash(gettext('You do not have permission to update this exam.'), 'error')
        return redirect(url_for('teacher.teacher_dashboard'))
    
    exam.title = request.form.get('title')
    exam.description = request.form.get('description')
    exam.questions_json = request.form.get('questions_json')
    exam.max_score = int(request.form.get('max_score', 100))
    exam.time_limit = int(request.form.get('time_limit', 60))
    exam.is_active = request.form.get('is_active') == 'on'
    
    due_date_str = request.form.get('due_date')
    if due_date_str:
        try:
            if 'T' in due_date_str:
                exam.due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            else:
                exam.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        except ValueError:
            flash(gettext('Invalid due date format.'), 'error')
            return redirect(url_for('teacher.show_edit_exam', exam_id=exam_id))
    else:
        exam.due_date = None
    
    db.session.commit()
    flash(gettext('Exam updated successfully!'), 'success')
    return redirect(url_for('teacher.view_course_exams', course_id=exam.course_id))

@teacher_bp.route('/exam/<int:exam_id>/toggle-status', methods=['POST'])
@require_role('teacher')
def toggle_exam_status(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    course = Course.query.filter_by(id=exam.course_id, teacher_id=current_user.id).first_or_404()
    
    # Toggle the active status
    exam.is_active = not exam.is_active
    db.session.commit()
    
    return '', 204  # Return no content for AJAX request

@teacher_bp.route('/exam/<int:exam_id>/reset-submissions', methods=['POST'])
@require_role('teacher')
def reset_exam_submissions(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    course = Course.query.filter_by(id=exam.course_id, teacher_id=current_user.id).first_or_404()
    
    # Delete all submissions for this exam
    deleted_count = ExamSubmission.query.filter_by(exam_id=exam_id).delete()
    db.session.commit()
    
    flash(gettext('Reset complete! %(count)s submission(s) cleared. Students can now retake this exam.', count=deleted_count), 'success')
    return redirect(url_for('teacher.view_course_exams', course_id=course.id))
@teacher_bp.route('/course/<int:course_id>/remove-student/<string:student_id>', methods=['POST'])
@require_role('teacher')
def remove_student(course_id, student_id):
    # Verify the teacher owns this course
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    
    try:
        sid = int(student_id)
    except (TypeError, ValueError):
        flash(gettext('Student is not enrolled in this course.'), 'error')
        return redirect(url_for('teacher.view_course', course_id=course_id))

    # Find the enrollment
    enrollment = Enrollment.query.filter_by(
        student_id=sid,
        course_id=course_id
    ).first()
    
    if not enrollment:
        flash(gettext('Student is not enrolled in this course.'), 'error')
        return redirect(url_for('teacher.view_course', course_id=course_id))
    
    # Get student name for flash message
    student = db.session.get(User, sid)
    student_name = (
        f"{student.first_name or gettext('Unknown')} {student.last_name or gettext('User')}"
        if student else gettext('Student')
    )
    
    # Remove the enrollment
    db.session.delete(enrollment)
    db.session.commit()
    
    flash(gettext('Successfully removed %(student)s from %(course)s.', student=student_name, course=course.title), 'success')
    return redirect(url_for('teacher.view_course', course_id=course_id))

@teacher_bp.route('/exam/<int:exam_id>/edit', methods=['POST'])
@require_role('teacher')
def edit_exam(exam_id):
    # Get the exam and verify teacher owns it through course ownership
    exam = Exam.query.get_or_404(exam_id)
    course = Course.query.filter_by(id=exam.course_id, teacher_id=current_user.id).first()
    
    if not course:
        flash(gettext('You do not have permission to edit this exam. Only the teacher who created the course can manage its exams.'), 'error')
        return redirect(url_for('teacher.teacher_dashboard'))
    
    # Update exam fields
    title = request.form.get('title')
    description = request.form.get('description')
    course_id = request.form.get('course_id')
    due_date_str = request.form.get('due_date')
    
    if not title:
        flash(gettext('Exam title is required.'), 'error')
        return redirect(url_for('teacher.teacher_dashboard'))
    
    # Verify new course also belongs to teacher if changed
    if course_id and int(course_id) != exam.course_id:
        new_course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first()
        if not new_course:
            flash(gettext('Invalid course selected.'), 'error')
            return redirect(url_for('teacher.teacher_dashboard'))
        exam.course_id = course_id
    
    exam.title = title
    exam.description = description
    
    # Handle due date
    due_date = None
    if due_date_str:
        try:
            # Handle both datetime-local format (YYYY-MM-DDTHH:MM) and date format (YYYY-MM-DD)
            if 'T' in due_date_str:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            else:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        except ValueError:
            flash(gettext('Invalid due date format.'), 'error')
            return redirect(url_for('teacher.teacher_dashboard'))
    exam.due_date = due_date
    
    db.session.commit()
    flash(gettext('Exam updated successfully!'), 'success')
    return redirect(url_for('teacher.view_course_exams', course_id=exam.course_id))

@teacher_bp.route('/exam/<int:exam_id>/delete', methods=['POST'])
@require_role('teacher')
def delete_exam(exam_id):
    # Get the exam and verify teacher owns it through course ownership
    exam = Exam.query.get_or_404(exam_id)
    course = Course.query.filter_by(id=exam.course_id, teacher_id=current_user.id).first()
    
    if not course:
        flash(gettext('You do not have permission to delete this exam. Only the teacher who created the course can manage its exams.'), 'error')
        return redirect(url_for('teacher.teacher_dashboard'))
    
    exam_title = exam.title
    course_id = exam.course_id
    db.session.delete(exam)
    db.session.commit()
    flash(gettext('Exam "%(title)s" deleted successfully!', title=exam_title), 'success')
    return redirect(url_for('teacher.view_course_exams', course_id=course_id))
# Quiz Management Routes
@teacher_bp.route('/course/<int:course_id>/quizzes')
@require_role('teacher')
def view_course_quizzes(course_id):
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    quizzes = Quiz.query.filter_by(course_id=course_id).order_by(Quiz.created_at.desc()).all()
    return render_template('teacher_course_quizzes.html', course=course, quizzes=quizzes, now=datetime.now())

@teacher_bp.route('/course/<int:course_id>/create-quiz', methods=['GET'])
@require_role('teacher')
def create_quiz(course_id):
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    # Redirect to multiple choice quiz creation (default)
    return redirect(url_for('teacher.create_mcq_quiz', course_id=course_id))

@teacher_bp.route('/course/<int:course_id>/create-mcq-quiz', methods=['GET', 'POST'])
@require_role('teacher')
def create_mcq_quiz(course_id):
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        quiz = Quiz()
        quiz.title = request.form.get('title')
        quiz.description = request.form.get('description')
        quiz.course_id = course_id
        quiz.quiz_type = 'multiple_choice'
        quiz.questions_json = request.form.get('questions_json', '[]')
        quiz.max_score = int(request.form.get('max_score', 100))
        quiz.time_limit = int(request.form.get('time_limit', 30))
        
        # Handle due date
        due_date_str = request.form.get('due_date')
        if due_date_str:
            quiz.due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
        
        quiz.is_active = request.form.get('is_active') == 'on'
        
        db.session.add(quiz)
        db.session.commit()
        
        flash(gettext('Multiple choice quiz created successfully!'), 'success')
        return redirect(url_for('teacher.view_course_quizzes', course_id=course_id))
    
    return render_template('teacher_create_mcq_quiz.html', course=course)

@teacher_bp.route('/quiz/<int:quiz_id>/edit-mcq', methods=['GET', 'POST'])
@require_role('teacher')
def edit_mcq_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    course = Course.query.filter_by(id=quiz.course_id, teacher_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        quiz.title = request.form.get('title')
        quiz.description = request.form.get('description')
        quiz.max_score = int(request.form.get('max_score', 100))
        quiz.time_limit = int(request.form.get('time_limit', 60))
        
        # Handle due date
        due_date_str = request.form.get('due_date')
        if due_date_str:
            quiz.due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
        else:
            quiz.due_date = None
            
        quiz.is_active = request.form.get('is_active') == 'on'
        
        # Check if questions_json is provided (new rich content format)
        questions_json = request.form.get('questions_json')
        if questions_json:
            # Use the rich content JSON format directly
            quiz.questions_json = questions_json
        else:
            # Fallback: Parse questions from individual form fields (legacy format)
            questions = []
            question_count = int(request.form.get('question_count', 0))
            
            for i in range(question_count):
                question_text = request.form.get(f'question_{i}')
                if question_text:
                    question = {
                        'question': question_text,
                        'options': {
                            'A': request.form.get(f'option_{i}_A', ''),
                            'B': request.form.get(f'option_{i}_B', ''),
                            'C': request.form.get(f'option_{i}_C', ''),
                            'D': request.form.get(f'option_{i}_D', '')
                        },
                        'correct_answer': request.form.get(f'correct_{i}', 'A'),
                        'explanation': request.form.get(f'explanation_{i}', '')
                    }
                    questions.append(question)
            
            quiz.questions_json = json.dumps(questions)
        
        quiz.updated_at = datetime.now()
        
        db.session.commit()
        flash(gettext('MCQ Quiz updated successfully!'), 'success')
        return redirect(url_for('teacher.view_course_quizzes', course_id=quiz.course_id))
    
    # Parse questions for display
    questions = []
    if quiz.questions_json:
        try:
            questions = json.loads(quiz.questions_json)
        except:
            questions = []
    
    return render_template('teacher_edit_mcq_quiz.html', quiz=quiz, course=course, questions=questions)

@teacher_bp.route('/quiz/<int:quiz_id>/submissions')
@require_role('teacher')
def view_quiz_submissions(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    course = Course.query.filter_by(id=quiz.course_id, teacher_id=current_user.id).first_or_404()
    # Eager load student relationships to avoid N+1 queries
    submissions = CodeSubmission.query.options(
        joinedload(CodeSubmission.student)
    ).filter_by(quiz_id=quiz_id).order_by(CodeSubmission.submitted_at.desc()).all()
    
    return render_template('teacher_quiz_submissions.html', quiz=quiz, course=course, submissions=submissions)

@teacher_bp.route('/submission/<int:submission_id>/grade', methods=['POST'])
@require_role('teacher')
def grade_submission(submission_id):
    submission = CodeSubmission.query.get_or_404(submission_id)
    quiz = Quiz.query.get_or_404(submission.quiz_id)
    course = Course.query.filter_by(id=quiz.course_id, teacher_id=current_user.id).first_or_404()
    
    submission.score = int(request.form.get('score', 0))
    submission.feedback = request.form.get('feedback', '')
    submission.status = 'graded'
    submission.graded_at = datetime.now()
    
    db.session.commit()
    
    flash(gettext('Submission graded successfully!'), 'success')
    return redirect(url_for('teacher.view_quiz_submissions', quiz_id=quiz.id))

@teacher_bp.route('/quiz/<int:quiz_id>/reset-submissions', methods=['POST'])
@require_role('teacher')
def reset_quiz_submissions(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    course = Course.query.filter_by(id=quiz.course_id, teacher_id=current_user.id).first_or_404()
    
    # Delete all submissions for this quiz
    deleted_count = CodeSubmission.query.filter_by(quiz_id=quiz_id).delete()
    db.session.commit()
    
    flash(gettext('Reset complete! %(count)s submission(s) cleared. Students can now retake this quiz.', count=deleted_count), 'success')
    return redirect(url_for('teacher.view_quiz_submissions', quiz_id=quiz.id))

@teacher_bp.route('/quiz/<int:quiz_id>/toggle-status', methods=['POST'])
@require_role('teacher')
def toggle_quiz_status(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    course = Course.query.filter_by(id=quiz.course_id, teacher_id=current_user.id).first_or_404()
    
    # Toggle the active status
    quiz.is_active = not quiz.is_active
    db.session.commit()
    
    return '', 204  # Return no content for AJAX request

@teacher_bp.route('/quiz/<int:quiz_id>/delete', methods=['POST'])
@require_role('teacher')
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    course = Course.query.filter_by(id=quiz.course_id, teacher_id=current_user.id).first_or_404()
    
    # Store course_id before deletion
    course_id = quiz.course_id
    
    try:
        # Delete all submissions for this quiz
        CodeSubmission.query.filter_by(quiz_id=quiz_id).delete()
        
        # Delete the quiz
        quiz_title = quiz.title
        db.session.delete(quiz)
        db.session.commit()
        
        flash(gettext('Quiz "%(title)s" deleted successfully!', title=quiz_title), 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(gettext('Error deleting quiz: %(err)s', err=str(e)), 'error')
    
    return redirect(url_for('teacher.view_course_quizzes', course_id=course_id))

