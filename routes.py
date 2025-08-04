from flask import session, render_template, request, redirect, url_for, flash, send_file
from flask_login import current_user, login_user
from app import app, db
from replit_auth import require_login, require_role, make_replit_blueprint
from models import User, StudentProfile, TeacherProfile, Course, Enrollment, Assignment
from datetime import datetime
import markdown
import weasyprint
import os
from werkzeug.utils import secure_filename

# Configure upload settings
UPLOAD_FOLDER = 'static/uploads/slides'
ALLOWED_EXTENSIONS = {'pdf', 'pptx'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def index():
    if current_user.is_authenticated:
        # Check if user has a role assigned
        if not current_user.role:
            return redirect(url_for('register_role'))
        
        # Redirect to appropriate dashboard based on role
        if current_user.role == 'student':
            return redirect(url_for('student_dashboard'))
        elif current_user.role == 'teacher':
            return redirect(url_for('teacher_dashboard'))
    
    return render_template('index.html')

@app.route('/register-role', methods=['GET', 'POST'])
@require_login
def register_role():
    # If user already has a role, redirect to dashboard
    if current_user.role:
        if current_user.role == 'student':
            return redirect(url_for('student_dashboard'))
        elif current_user.role == 'teacher':
            return redirect(url_for('teacher_dashboard'))
    
    if request.method == 'POST':
        role = request.form.get('role')
        
        if role not in ['student', 'teacher']:
            flash('Please select a valid role.', 'error')
            return render_template('register_role.html')
        
        # Update user role
        current_user.role = role
        db.session.commit()
        
        # Create role-specific profile
        if role == 'student':
            student_profile = StudentProfile()
            student_profile.user_id = current_user.id
            student_profile.student_id = f"STU{current_user.id[:8]}"
            student_profile.grade_level = request.form.get('grade_level', '9th Grade')
            db.session.add(student_profile)
        elif role == 'teacher':
            teacher_profile = TeacherProfile()
            teacher_profile.user_id = current_user.id
            teacher_profile.employee_id = f"EMP{current_user.id[:8]}"
            teacher_profile.department = request.form.get('department', 'General')
            db.session.add(teacher_profile)
        
        db.session.commit()
        flash(f'Welcome! You have been registered as a {role}.', 'success')
        
        # Redirect to appropriate dashboard
        if role == 'student':
            return redirect(url_for('student_dashboard'))
        else:
            return redirect(url_for('teacher_dashboard'))
    
    return render_template('register_role.html')

@app.route('/student/dashboard')
@require_role('student')
def student_dashboard():
    # Get student's enrollments and assignments
    enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
    enrolled_courses = [enrollment.course for enrollment in enrollments]
    
    # Get assignments for enrolled courses
    assignments = []
    for course in enrolled_courses:
        course_assignments = Assignment.query.filter_by(course_id=course.id).all()
        assignments.extend(course_assignments)
    
    # Sort assignments by due date
    assignments.sort(key=lambda x: x.due_date if x.due_date else datetime.max)
    
    return render_template('student_dashboard.html', 
                         courses=enrolled_courses, 
                         assignments=assignments[:5])  # Show only next 5 assignments

@app.route('/teacher/dashboard')
@require_role('teacher')
def teacher_dashboard():
    # Get teacher's courses
    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    
    # Get recent assignments
    assignments = []
    for course in courses:
        course_assignments = Assignment.query.filter_by(course_id=course.id).all()
        assignments.extend(course_assignments)
    
    # Sort assignments by creation date
    assignments.sort(key=lambda x: x.created_at, reverse=True)
    
    # Get total student count across all courses
    total_students = 0
    for course in courses:
        total_students += len(course.enrollments)
    
    return render_template('teacher_dashboard.html', 
                         courses=courses, 
                         assignments=assignments[:5],
                         total_students=total_students)

@app.route('/teacher/create-course', methods=['GET', 'POST'])
@require_role('teacher')
def create_course():
    if request.method == 'POST':
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
            flash('Course title is required.', 'error')
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
                    
                    flash(f'Course slide file "{filename}" uploaded successfully!', 'success')
                    
                except Exception as e:
                    flash(f'Error uploading file: {str(e)}', 'error')
        
        db.session.add(course)
        db.session.commit()
        
        flash('Programming course created successfully!', 'success')
        return redirect(url_for('teacher_dashboard'))
    
    return render_template('teacher_create_course.html')

@app.route('/teacher/course/<int:course_id>')
@require_role('teacher')
def view_course(course_id):
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    # Convert markdown to HTML for preview
    content_html = markdown.markdown(course.content or '', extensions=['codehilite', 'fenced_code']) if course.content else ''
    return render_template('teacher_view_course.html', course=course, content_html=content_html)

@app.route('/teacher/course/<int:course_id>/edit', methods=['GET', 'POST'])
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
                    
                    flash(f'Course slide file "{filename}" uploaded successfully!', 'success')
                    
                except Exception as e:
                    flash(f'Error uploading file: {str(e)}', 'error')
        
        db.session.commit()
        flash('Course updated successfully!', 'success')
        return redirect(url_for('view_course', course_id=course.id))
    
    return render_template('teacher_edit_course.html', course=course)

@app.route('/course/<int:course_id>/download-slides')
@require_login
def download_course_slides(course_id):
    # Check access permissions
    if current_user.role == 'teacher':
        course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    else:
        # Student access - check enrollment
        enrollment = Enrollment.query.filter_by(course_id=course_id, student_id=current_user.id).first()
        if not enrollment:
            flash('You are not enrolled in this course.', 'error')
            return redirect(url_for('student_dashboard'))
        course = Course.query.get_or_404(course_id)
    
    if not course.uploaded_file_path or not os.path.exists(course.uploaded_file_path):
        flash('No slide file available for this course.', 'error')
        if current_user.role == 'teacher':
            return redirect(url_for('view_course', course_id=course.id))
        else:
            return redirect(url_for('student_dashboard'))
    
    return send_file(course.uploaded_file_path, as_attachment=True, download_name=course.uploaded_file_name)

@app.route('/teacher/course/<int:course_id>/generate-pdf', methods=['POST'])
@require_role('teacher')
def generate_course_pdf(course_id):
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    
    try:
        # Create PDF directory if it doesn't exist
        pdf_dir = os.path.join(app.instance_path, 'pdfs')
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
        
        flash('PDF generated successfully!', 'success')
        return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)
        
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('view_course', course_id=course.id))

@app.route('/teacher/course/<int:course_id>/download-pdf')
@require_role('teacher')
def download_course_pdf(course_id):
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    
    if not course.pdf_generated or not course.pdf_path or not os.path.exists(course.pdf_path):
        flash('PDF not available. Please generate it first.', 'error')
        return redirect(url_for('view_course', course_id=course.id))
    
    pdf_filename = f"course_{course_id}_{secure_filename(course.title)}.pdf"
    return send_file(course.pdf_path, as_attachment=True, download_name=pdf_filename)

@app.route('/student/course/<int:course_id>/download-pdf')
@require_role('student')
def student_download_course_pdf(course_id):
    # Check if student is enrolled in the course
    enrollment = Enrollment.query.filter_by(course_id=course_id, student_id=current_user.id).first()
    if not enrollment:
        flash('You are not enrolled in this course.', 'error')
        return redirect(url_for('student_dashboard'))
    
    course = Course.query.get_or_404(course_id)
    
    # Generate PDF if it doesn't exist or regenerate it
    try:
        # Ensure pdf directory exists
        pdf_dir = os.path.join(app.root_path, 'static', 'pdfs')
        os.makedirs(pdf_dir, exist_ok=True)
        
        # Convert markdown to HTML
        content_html = markdown.markdown(
            course.content or 'No content available.',
            extensions=['codehilite', 'fenced_code']
        )
        
        # Create HTML template for PDF
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
        
        # Generate PDF
        pdf_filename = f"course_{course_id}_{secure_filename(course.title)}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        
        # Create PDF from HTML using WeasyPrint
        weasyprint.HTML(string=html_content).write_pdf(pdf_path)
        
        return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)
        
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('student_dashboard'))

@app.route('/course/<int:course_id>/slides')
def view_course_slides(course_id):
    # Check authentication but handle gracefully
    if not current_user.is_authenticated:
        return redirect(url_for('replit_auth.login'))
    
    # Check if user is enrolled or is the teacher
    if current_user.role == 'teacher':
        course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    else:
        # Student access - check enrollment
        enrollment = Enrollment.query.filter_by(course_id=course_id, student_id=current_user.id).first()
        if not enrollment:
            flash('You are not enrolled in this course.', 'error')
            return redirect(url_for('student_dashboard'))
        course = Course.query.get_or_404(course_id)
    
    return render_template('course_slides.html', course=course)

@app.route('/course/<int:course_id>/slides/data')
def get_course_slides_data(course_id):
    # For demo purposes, allow public access to slides data
    course = Course.query.get_or_404(course_id)
    
    # Convert markdown to reveal.js compatible format
    slides_content = convert_markdown_to_slides(course.content or '')
    
    return {
        'title': course.title,
        'content': slides_content,
        'programming_language': course.programming_language,
        'difficulty_level': course.difficulty_level
    }

def convert_markdown_to_slides(markdown_content):
    """Convert markdown content to reveal.js slide format"""
    if not markdown_content:
        return "<section><h1>No content available</h1></section>"
    
    # Split content by major headings (# and ##)
    lines = markdown_content.split('\n')
    slides = []
    current_slide = []
    
    for line in lines:
        # New slide on # heading
        if line.startswith('# '):
            if current_slide:
                slides.append('\n'.join(current_slide))
                current_slide = []
            current_slide.append(line)
        # New vertical slide on ## heading  
        elif line.startswith('## '):
            if current_slide:
                slides.append('\n'.join(current_slide))
                current_slide = []
            current_slide.append(line)
        else:
            current_slide.append(line)
    
    # Add the last slide
    if current_slide:
        slides.append('\n'.join(current_slide))
    
    # Convert each slide markdown to HTML
    html_slides = []
    for slide_md in slides:
        if slide_md.strip():
            # Convert markdown to HTML
            slide_html = markdown.markdown(slide_md, extensions=['codehilite', 'fenced_code'])
            html_slides.append(f'<section>{slide_html}</section>')
    
    return '\n'.join(html_slides) if html_slides else "<section><h1>No content available</h1></section>"

@app.route('/teacher/create-assignment', methods=['POST'])
@require_role('teacher')
def create_assignment():
    title = request.form.get('title')
    description = request.form.get('description')
    course_id = request.form.get('course_id')
    due_date_str = request.form.get('due_date')
    
    if not title or not course_id:
        flash('Assignment title and course are required.', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    # Verify teacher owns the course
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first()
    if not course:
        flash('Invalid course selected.', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid due date format.', 'error')
            return redirect(url_for('teacher_dashboard'))
    
    assignment = Assignment()
    assignment.title = title
    assignment.description = description
    assignment.course_id = course_id
    assignment.due_date = due_date
    db.session.add(assignment)
    db.session.commit()
    
    flash('Assignment created successfully!', 'success')
    return redirect(url_for('teacher_dashboard'))

@app.route('/student/enroll', methods=['POST'])
@require_role('student')
def enroll_course():
    course_id = request.form.get('course_id')
    
    if not course_id:
        flash('Course ID is required.', 'error')
        return redirect(url_for('student_dashboard'))
    
    # Check if course exists
    course = Course.query.get(course_id)
    if not course:
        flash('Course not found.', 'error')
        return redirect(url_for('student_dashboard'))
    
    # Check if already enrolled
    existing_enrollment = Enrollment.query.filter_by(
        student_id=current_user.id, 
        course_id=course_id
    ).first()
    
    if existing_enrollment:
        flash('You are already enrolled in this course.', 'warning')
        return redirect(url_for('student_dashboard'))
    
    enrollment = Enrollment()
    enrollment.student_id = current_user.id
    enrollment.course_id = course_id
    db.session.add(enrollment)
    db.session.commit()
    
    flash(f'Successfully enrolled in {course.title}!', 'success')
    return redirect(url_for('student_dashboard'))

@app.route('/courses')
@require_login
def browse_courses():
    courses = Course.query.all()
    return render_template('browse_courses.html', courses=courses)

@app.route('/test-login', methods=['GET', 'POST'])
def test_login():
    """Development-only route for quick testing with predefined users"""
    if request.method == 'POST':
        test_user = request.form.get('test_user')
        
        if test_user == 'teacher':
            user = User.query.get('teacher_test_001')
        elif test_user == 'student':
            user = User.query.get('student_test_001')
        else:
            flash('Invalid test user selected.', 'error')
            return redirect(url_for('test_login'))
        
        if user:
            login_user(user)
            flash(f'Logged in as {user.first_name} {user.last_name} ({user.role})', 'success')
            
            # Redirect to appropriate dashboard
            if user.role == 'student':
                return redirect(url_for('student_dashboard'))
            elif user.role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
        else:
            flash('Test user not found.', 'error')
            return redirect(url_for('test_login'))
    
    return render_template('test_login.html')

@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404
