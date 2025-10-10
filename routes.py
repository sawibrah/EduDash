from flask import session, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import current_user, login_user, logout_user
from sqlalchemy.orm import joinedload
from app import app, db, csrf
from auth import require_login, require_role
from forms import RegistrationForm, LoginForm, ProfileForm
from models import User, StudentProfile, TeacherProfile, Course, Enrollment, Exam, ExamSubmission, Quiz, CodeSubmission
from datetime import datetime
import json
import markdown
import bleach
import weasyprint
import os
from werkzeug.utils import secure_filename

# Configure upload settings
UPLOAD_FOLDER = 'static/uploads/slides'
ALLOWED_EXTENSIONS = {'pdf', 'pptx'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Remove Replit OAuth blueprint

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

# Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Create new user - all new registrations default to student role for security
        # Teachers must be manually promoted by administrators
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role='student'  # Force student role - teachers require admin approval
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        # Create student profile for all new users
        student_profile = StudentProfile(
            user_id=user.id,
            student_id=f"STU{user.id:08d}",
            grade_level=form.grade_level.data if form.grade_level.data else '9th Grade'
        )
        db.session.add(student_profile)
        
        db.session.commit()
        flash(f'Registration successful! Welcome, {user.first_name}!', 'success')
        login_user(user)
        
        return redirect(url_for('student_dashboard'))
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.first_name}!', 'success')
            
            if next_page:
                return redirect(next_page)
            elif user.role == 'student':
                return redirect(url_for('student_dashboard'))
            else:
                return redirect(url_for('teacher_dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@require_login
def logout():
    user_name = current_user.first_name
    logout_user()
    flash(f'You have been logged out, {user_name}. See you next time!', 'info')
    return redirect(url_for('index'))

@app.route('/')
def index():
    if current_user.is_authenticated:
        # Redirect to appropriate dashboard based on role
        if current_user.role == 'student':
            return redirect(url_for('student_dashboard'))
        elif current_user.role == 'teacher':
            return redirect(url_for('teacher_dashboard'))
    
    return render_template('index.html')



@app.route('/student/dashboard')
@require_role('student')
def student_dashboard():
    # Get student's enrollments with eager loading to avoid N+1 queries
    enrollments = Enrollment.query.options(
        joinedload(Enrollment.course).joinedload(Course.teacher)
    ).filter_by(student_id=current_user.id).all()
    enrolled_courses = [enrollment.course for enrollment in enrollments]
    
    # Get exams for enrolled courses with eager loading
    course_ids = [course.id for course in enrolled_courses]
    exams = Exam.query.options(
        joinedload(Exam.course)
    ).filter(Exam.course_id.in_(course_ids)).all() if course_ids else []
    
    # Sort exams by due date
    exams.sort(key=lambda x: x.due_date if x.due_date else datetime.max)
    
    # Get available quizzes for enrolled courses with eager loading
    quizzes = Quiz.query.options(
        joinedload(Quiz.course)
    ).filter(
        Quiz.course_id.in_(course_ids),
        Quiz.is_active == True
    ).all() if course_ids else []
    
    # Filter out quizzes already submitted
    submitted_quiz_ids = [s.quiz_id for s in CodeSubmission.query.filter_by(student_id=current_user.id).all()]
    quizzes = [q for q in quizzes if q.id not in submitted_quiz_ids]
    
    # Sort quizzes by due date
    quizzes.sort(key=lambda x: x.due_date if x.due_date else datetime.max)
    
    return render_template('student_dashboard.html', 
                         courses=enrolled_courses, 
                         exams=exams[:5],
                         quizzes=quizzes[:5])  # Show only next 5 exams and quizzes

@app.route('/teacher/dashboard')
@require_role('teacher')
def teacher_dashboard():
    # Get teacher's courses with eager loading to avoid N+1 queries
    courses = Course.query.options(
        joinedload(Course.enrollments)
    ).filter_by(teacher_id=current_user.id).all()
    
    # Get course IDs for efficient querying
    course_ids = [course.id for course in courses]
    
    # Get recent exams with eager loading
    exams = Exam.query.options(
        joinedload(Exam.course)
    ).filter(Exam.course_id.in_(course_ids)).order_by(Exam.created_at.desc()).limit(5).all() if course_ids else []
    
    # Get total student count across all courses (already loaded with joinedload)
    total_students = sum(len(course.enrollments) for course in courses)
    
    # Get recent quizzes with eager loading
    quizzes = Quiz.query.options(
        joinedload(Quiz.course)
    ).filter(Quiz.course_id.in_(course_ids)).order_by(Quiz.created_at.desc()).limit(5).all() if course_ids else []
    
    return render_template('teacher_dashboard.html', 
                         courses=courses, 
                         exams=exams,
                         quizzes=quizzes,
                         total_students=total_students)

def generate_5_slide_template(title="", programming_language=""):
    """Generate a 5-slide markdown template for courses"""
    lang_lower = programming_language.lower() if programming_language else "programming"
    
    template = f"""# {title or "Course Title"}

---

## Slide 1: Introduction
### Welcome to {title or "Your Course"}

**Course Overview:**
- Learn {programming_language or "programming"} fundamentals
- Build practical projects
- Master key concepts step-by-step

**What You'll Achieve:**
- Write your first {lang_lower} program
- Understand core programming concepts
- Create real-world applications

```{lang_lower}
# Welcome! Let's start coding
print("Hello, {programming_language or "World"}!")
```

---

## Slide 2: Getting Started
### Setting Up Your Environment

**Prerequisites:**
- Basic computer skills
- Curiosity to learn
- No prior {lang_lower} experience needed

**Tools We'll Use:**
- Code editor (VS Code recommended)
- {programming_language or "Programming"} interpreter
- Project files and examples

**First Steps:**
1. Install the development environment
2. Write your first program
3. Run and test your code

```{lang_lower}
# Your first {lang_lower} program
def hello_world():
    return "Welcome to {programming_language or "programming"}!"
```

---

## Slide 3: Core Concepts
### Fundamental Building Blocks

**Key Topics Covered:**
- Variables and data types
- Functions and methods
- Control structures (if/else, loops)
- Data structures (lists, dictionaries)

**Hands-On Practice:**
- Interactive coding exercises
- Step-by-step examples
- Common patterns and best practices

```{lang_lower}
# Example: Working with variables
name = "Student"
age = 25
skills = ["{lang_lower}", "problem-solving", "creativity"]

print(f"{{name}} is {{age}} years old")
print(f"Skills: {{', '.join(skills)}}")
```

---

## Slide 4: Practical Projects
### Building Real Applications

**Project Examples:**
- Calculator application
- Data analysis tool
- Web scraper
- Game or interactive program

**Skills You'll Develop:**
- Problem-solving approach
- Code organization
- Testing and debugging
- Best practices

```{lang_lower}
# Example: Simple calculator
def calculator(num1, num2, operation):
    if operation == "+":
        return num1 + num2
    elif operation == "-":
        return num1 - num2
    else:
        return "Unknown operation"

# Usage
result = calculator(10, 5, "+")
print(f"Result: {{result}}")
```

---

## Slide 5: Next Steps
### Continue Your Learning Journey

**What You've Learned:**
- {programming_language or "Programming"} fundamentals
- Practical coding skills
- Problem-solving techniques
- Real project experience

**Continue Learning:**
- Practice with more projects
- Explore advanced topics
- Join coding communities
- Build your portfolio

**Resources:**
- Official {programming_language or "programming"} documentation
- Online coding platforms
- Open source projects
- Developer communities

```{lang_lower}
# Keep coding and learning!
print("Congratulations on completing the course!")
print("Your {lang_lower} journey has just begun!")
```

**Ready to take on new challenges? Keep coding!** 🚀"""
    
    return template

@app.route('/teacher/create-course', methods=['GET', 'POST'])
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

@app.route('/teacher/course/<int:course_id>/students')
@require_role('teacher')
def view_course_students(course_id):
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    # Eager load student relationships to avoid N+1 queries
    enrollments = Enrollment.query.options(
        joinedload(Enrollment.student)
    ).filter_by(course_id=course_id).all()
    return render_template('teacher_course_students.html', course=course, enrollments=enrollments)

@app.route('/teacher/course/<int:course_id>/exams')
@require_role('teacher')
def view_course_exams(course_id):
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    exams = Exam.query.filter_by(course_id=course_id).order_by(Exam.created_at.desc()).all()
    return render_template('teacher_course_exams.html', course=course, exams=exams, now=datetime.now())

@app.route('/teacher/course/<int:course_id>/create-exam')
@require_role('teacher')
def show_create_exam(course_id):
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    return render_template('teacher_create_exam.html', course=course)

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

@app.route('/teacher/course/<int:course_id>/delete', methods=['POST'])
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
        
        flash(f'Course "{course_title}" deleted successfully!', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting course: {str(e)}', 'error')
    
    return redirect(url_for('teacher_dashboard'))

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

@app.route('/course/<int:course_id>/view-file')
@require_login
def view_course_file(course_id):
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
    
    # Return file for inline viewing (not as attachment)
    return send_file(course.uploaded_file_path, as_attachment=False)

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

@app.route('/teacher/create-exam', methods=['POST'])
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
        flash('Exam title is required.', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    if not course_id:
        flash('Course ID is required.', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    # Verify teacher owns the course
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first()
    if not course:
        flash('Invalid course selected.', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    due_date = None
    if due_date_str:
        try:
            if 'T' in due_date_str:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            else:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid due date format.', 'error')
            return redirect(url_for('show_create_exam', course_id=course_id))
    
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
    
    flash('Exam created successfully!', 'success')
    return redirect(url_for('view_course_exams', course_id=course_id))

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

@app.route('/teacher/course/<int:course_id>/remove-student/<string:student_id>', methods=['POST'])
@require_role('teacher')
def remove_student(course_id, student_id):
    # Verify the teacher owns this course
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    
    # Find the enrollment
    enrollment = Enrollment.query.filter_by(
        student_id=student_id,
        course_id=course_id
    ).first()
    
    if not enrollment:
        flash('Student is not enrolled in this course.', 'error')
        return redirect(url_for('view_course', course_id=course_id))
    
    # Get student name for flash message
    student = User.query.get(student_id)
    student_name = f"{student.first_name or 'Unknown'} {student.last_name or 'User'}" if student else "Student"
    
    # Remove the enrollment
    db.session.delete(enrollment)
    db.session.commit()
    
    flash(f'Successfully removed {student_name} from {course.title}.', 'success')
    return redirect(url_for('view_course', course_id=course_id))

@app.route('/teacher/exam/<int:exam_id>/edit', methods=['POST'])
@require_role('teacher')
def edit_exam(exam_id):
    # Get the exam and verify teacher owns it through course ownership
    exam = Exam.query.get_or_404(exam_id)
    course = Course.query.filter_by(id=exam.course_id, teacher_id=current_user.id).first()
    
    if not course:
        flash('You do not have permission to edit this exam. Only the teacher who created the course can manage its exams.', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    # Update exam fields
    title = request.form.get('title')
    description = request.form.get('description')
    course_id = request.form.get('course_id')
    due_date_str = request.form.get('due_date')
    
    if not title:
        flash('Exam title is required.', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    # Verify new course also belongs to teacher if changed
    if course_id and int(course_id) != exam.course_id:
        new_course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first()
        if not new_course:
            flash('Invalid course selected.', 'error')
            return redirect(url_for('teacher_dashboard'))
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
            flash('Invalid due date format.', 'error')
            return redirect(url_for('teacher_dashboard'))
    exam.due_date = due_date
    
    db.session.commit()
    flash('Exam updated successfully!', 'success')
    return redirect(url_for('view_course_exams', course_id=exam.course_id))

@app.route('/teacher/exam/<int:exam_id>/delete', methods=['POST'])
@require_role('teacher')
def delete_exam(exam_id):
    # Get the exam and verify teacher owns it through course ownership
    exam = Exam.query.get_or_404(exam_id)
    course = Course.query.filter_by(id=exam.course_id, teacher_id=current_user.id).first()
    
    if not course:
        flash('You do not have permission to delete this exam. Only the teacher who created the course can manage its exams.', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    exam_title = exam.title
    db.session.delete(exam)
    db.session.commit()
    
    course_id = exam.course_id
    flash(f'Exam "{exam_title}" deleted successfully!', 'success')
    return redirect(url_for('view_course_exams', course_id=course_id))

@app.route('/api/available-courses')
@require_role('student')
@csrf.exempt
def available_courses_api():
    # Get all published courses that the student is not already enrolled in
    enrolled_course_ids = [enrollment.course_id for enrollment in 
                          Enrollment.query.filter_by(student_id=current_user.id).all()]
    
    # Eager load teacher relationships to avoid N+1 queries
    available_courses = Course.query.options(
        joinedload(Course.teacher)
    ).filter(
        Course.course_status == 'published',
        ~Course.id.in_(enrolled_course_ids)
    ).all()
    
    courses_data = []
    for course in available_courses:
        courses_data.append({
            'id': course.id,
            'title': course.title,
            'description': course.description,
            'programming_language': course.programming_language,
            'difficulty_level': course.difficulty_level,
            'estimated_hours': course.estimated_hours,
            'teacher_name': f"{course.teacher.first_name} {course.teacher.last_name}" if course.teacher else "Unknown"
        })
    
    return jsonify(courses_data)

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

# Quiz Management Routes
@app.route('/teacher/course/<int:course_id>/quizzes')
@require_role('teacher')
def view_course_quizzes(course_id):
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    quizzes = Quiz.query.filter_by(course_id=course_id).order_by(Quiz.created_at.desc()).all()
    return render_template('teacher_course_quizzes.html', course=course, quizzes=quizzes, now=datetime.now())

@app.route('/teacher/course/<int:course_id>/create-quiz', methods=['GET'])
@require_role('teacher')
def create_quiz(course_id):
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    # Redirect to multiple choice quiz creation (default)
    return redirect(url_for('create_mcq_quiz', course_id=course_id))

@app.route('/teacher/course/<int:course_id>/create-mcq-quiz', methods=['GET', 'POST'])
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
        
        flash('Multiple choice quiz created successfully!', 'success')
        return redirect(url_for('view_course_quizzes', course_id=course_id))
    
    return render_template('teacher_create_mcq_quiz.html', course=course)

@app.route('/teacher/course/<int:course_id>/create-coding-quiz', methods=['GET', 'POST'])
@require_role('teacher')
def create_coding_quiz(course_id):
    course = Course.query.filter_by(id=course_id, teacher_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        quiz = Quiz()
        quiz.title = request.form.get('title')
        quiz.description = request.form.get('description')
        quiz.course_id = course_id
        quiz.quiz_type = 'coding'
        quiz.programming_language = request.form.get('programming_language') or course.programming_language
        quiz.starter_code = request.form.get('starter_code', '')
        quiz.expected_output = request.form.get('expected_output', '')
        quiz.instructions = request.form.get('instructions', '')
        quiz.max_score = int(request.form.get('max_score', 100))
        quiz.time_limit = int(request.form.get('time_limit', 60))
        
        # Handle due date
        due_date_str = request.form.get('due_date')
        if due_date_str:
            quiz.due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
        
        quiz.is_active = request.form.get('is_active') == 'on'
        
        db.session.add(quiz)
        db.session.commit()
        
        flash('Coding quiz created successfully!', 'success')
        return redirect(url_for('view_course_quizzes', course_id=course_id))
    
    # Create default template values based on programming language
    lang = course.programming_language or 'Python'
    lang_lower = lang.lower()
    
    if lang == 'Python':
        default_instructions = """Write a function called 'fibonacci' that takes an integer n as input and returns the nth number in the Fibonacci sequence.

Requirements:
- Function should handle n >= 0
- Use efficient algorithm
- Include proper error handling

Test cases:
- fibonacci(0) should return 0
- fibonacci(1) should return 1
- fibonacci(5) should return 5"""
        
        default_starter_code = """# Provide starter code or function template for students

def fibonacci(n):
    # Your code here
    pass

# Test your function
print(fibonacci(5))"""
        
        default_expected_output = "5"
        
    elif lang == 'JavaScript':
        default_instructions = """Write a function called 'fibonacci' that takes an integer n as input and returns the nth number in the Fibonacci sequence.

Requirements:
- Function should handle n >= 0
- Use efficient algorithm
- Include proper error handling

Test cases:
- fibonacci(0) should return 0
- fibonacci(1) should return 1
- fibonacci(5) should return 5"""
        
        default_starter_code = """// Provide starter code or function template for students

function fibonacci(n) {
    // Your code here
}

// Test your function
console.log(fibonacci(5));"""
        
        default_expected_output = "5"
        
    elif lang == 'Java':
        default_instructions = """Write a method called 'fibonacci' that takes an integer n as input and returns the nth number in the Fibonacci sequence.

Requirements:
- Method should handle n >= 0
- Use efficient algorithm
- Include proper error handling

Test cases:
- fibonacci(0) should return 0
- fibonacci(1) should return 1
- fibonacci(5) should return 5"""
        
        default_starter_code = """// Provide starter code or method template for students

public class Solution {
    public static int fibonacci(int n) {
        // Your code here
        return 0;
    }
    
    public static void main(String[] args) {
        System.out.println(fibonacci(5));
    }
}"""
        
        default_expected_output = "5"
        
    elif lang == 'C++':
        default_instructions = """Write a C++ function called 'fibonacci' that takes an integer n as input and returns the nth number in the Fibonacci sequence.

Requirements:
- Function should handle n >= 0
- Use efficient algorithm
- Include proper error handling

Test cases:
- fibonacci(0) should return 0
- fibonacci(1) should return 1
- fibonacci(5) should return 5"""
        
        default_starter_code = """// Provide starter code or function template for students
#include <iostream>
using namespace std;

int fibonacci(int n) {
    // Your code here
    return 0;
}

int main() {
    cout << fibonacci(5) << endl;
    return 0;
}"""
        
        default_expected_output = "5"
        
    elif lang == 'C#':
        default_instructions = """Write a C# method called 'Fibonacci' that takes an integer n as input and returns the nth number in the Fibonacci sequence.

Requirements:
- Method should handle n >= 0
- Use efficient algorithm
- Include proper error handling

Test cases:
- Fibonacci(0) should return 0
- Fibonacci(1) should return 1
- Fibonacci(5) should return 5"""
        
        default_starter_code = """// Provide starter code or method template for students
using System;

class Program {
    public static int Fibonacci(int n) {
        // Your code here
        return 0;
    }
    
    static void Main() {
        Console.WriteLine(Fibonacci(5));
    }
}"""
        
        default_expected_output = "5"
        
    else:
        # Generic template for other languages
        default_instructions = f"""Write a program in {lang} that solves a specific problem.

Requirements:
- Follow proper {lang} syntax
- Include appropriate error handling
- Test your solution thoroughly

Provide clear implementation and test cases."""
        
        default_starter_code = f"""// {lang} code template
// Write your solution here

// Test your code"""
        
        default_expected_output = "Expected output here"
    
    # Pass default values to template
    defaults = {
        'instructions': default_instructions,
        'starter_code': default_starter_code,
        'expected_output': default_expected_output
    }
    
    return render_template('teacher_create_quiz.html', course=course, defaults=defaults)

@app.route('/teacher/quiz/<int:quiz_id>/edit', methods=['GET', 'POST'])
@require_role('teacher')
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    course = Course.query.filter_by(id=quiz.course_id, teacher_id=current_user.id).first_or_404()
    
    # Redirect to appropriate edit page based on quiz type
    if quiz.quiz_type == 'multiple_choice':
        return redirect(url_for('edit_mcq_quiz', quiz_id=quiz_id))
    
    if request.method == 'POST':
        quiz.title = request.form.get('title')
        quiz.description = request.form.get('description')
        quiz.programming_language = request.form.get('programming_language')
        quiz.starter_code = request.form.get('starter_code', '')
        quiz.expected_output = request.form.get('expected_output', '')
        quiz.instructions = request.form.get('instructions', '')
        quiz.max_score = int(request.form.get('max_score', 100))
        quiz.time_limit = int(request.form.get('time_limit', 60))
        
        # Handle due date
        due_date_str = request.form.get('due_date')
        if due_date_str:
            quiz.due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
        else:
            quiz.due_date = None
            
        quiz.is_active = request.form.get('is_active') == 'on'
        quiz.updated_at = datetime.now()
        
        db.session.commit()
        flash('Quiz updated successfully!', 'success')
        return redirect(url_for('view_course_quizzes', course_id=quiz.course_id))
    
    return render_template('teacher_edit_quiz.html', quiz=quiz, course=course)

@app.route('/teacher/quiz/<int:quiz_id>/edit-mcq', methods=['GET', 'POST'])
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
        
        # Parse questions from form
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
        flash('MCQ Quiz updated successfully!', 'success')
        return redirect(url_for('view_course_quizzes', course_id=quiz.course_id))
    
    # Parse questions for display
    questions = []
    if quiz.questions_json:
        try:
            questions = json.loads(quiz.questions_json)
        except:
            questions = []
    
    return render_template('teacher_edit_mcq_quiz.html', quiz=quiz, course=course, questions=questions)

@app.route('/teacher/quiz/<int:quiz_id>/submissions')
@require_role('teacher')
def view_quiz_submissions(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    course = Course.query.filter_by(id=quiz.course_id, teacher_id=current_user.id).first_or_404()
    # Eager load student relationships to avoid N+1 queries
    submissions = CodeSubmission.query.options(
        joinedload(CodeSubmission.student)
    ).filter_by(quiz_id=quiz_id).order_by(CodeSubmission.submitted_at.desc()).all()
    
    return render_template('teacher_quiz_submissions.html', quiz=quiz, course=course, submissions=submissions)

@app.route('/teacher/submission/<int:submission_id>/grade', methods=['POST'])
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
    
    flash('Submission graded successfully!', 'success')
    return redirect(url_for('view_quiz_submissions', quiz_id=quiz.id))

@app.route('/teacher/quiz/<int:quiz_id>/reset-submissions', methods=['POST'])
@require_role('teacher')
def reset_quiz_submissions(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    course = Course.query.filter_by(id=quiz.course_id, teacher_id=current_user.id).first_or_404()
    
    # Delete all submissions for this quiz
    deleted_count = CodeSubmission.query.filter_by(quiz_id=quiz_id).delete()
    db.session.commit()
    
    flash(f'Reset complete! {deleted_count} submission(s) cleared. Students can now retake this quiz.', 'success')
    return redirect(url_for('view_quiz_submissions', quiz_id=quiz.id))

@app.route('/teacher/quiz/<int:quiz_id>/toggle-status', methods=['POST'])
@require_role('teacher')
def toggle_quiz_status(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    course = Course.query.filter_by(id=quiz.course_id, teacher_id=current_user.id).first_or_404()
    
    # Toggle the active status
    quiz.is_active = not quiz.is_active
    db.session.commit()
    
    return '', 204  # Return no content for AJAX request

# Student Quiz Routes
@app.route('/quiz/<int:quiz_id>')
@require_role('student')
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if student is enrolled in the course
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=quiz.course_id
    ).first()
    
    if not enrollment:
        flash('You are not enrolled in this course.', 'error')
        return redirect(url_for('student_dashboard'))
    
    # Check if quiz is active and not past due date
    if not quiz.is_active:
        flash('This quiz is not currently active.', 'error')
        return redirect(url_for('student_dashboard'))
    
    if quiz.due_date and datetime.now() > quiz.due_date:
        flash('This quiz is past its due date.', 'error')
        return redirect(url_for('student_dashboard'))
    
    # Check if student has already submitted
    existing_submission = CodeSubmission.query.filter_by(
        quiz_id=quiz_id,
        student_id=current_user.id
    ).first()
    
    if existing_submission:
        return render_template('student_quiz_submitted.html', 
                             quiz=quiz, 
                             submission=existing_submission)
    
    # Render different templates based on quiz type
    if quiz.quiz_type == 'multiple_choice':
        return render_template('student_take_mcq_quiz.html', quiz=quiz)
    else:
        return render_template('student_take_quiz.html', quiz=quiz)

@app.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
@require_role('student')
@csrf.exempt
def submit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if student is enrolled
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=quiz.course_id
    ).first()
    
    if not enrollment:
        return jsonify({'success': False, 'error': 'Not enrolled in course'})
    
    # Check if already submitted
    existing_submission = CodeSubmission.query.filter_by(
        quiz_id=quiz_id,
        student_id=current_user.id
    ).first()
    
    if existing_submission:
        return jsonify({'success': False, 'error': 'Already submitted'})
    
    # Get submission data from request
    data = request.get_json()
    
    # Create submission
    submission = CodeSubmission()
    submission.quiz_id = quiz_id
    submission.student_id = current_user.id
    submission.submitted_at = datetime.now()
    
    # Handle different quiz types
    if quiz.quiz_type == 'multiple_choice':
        # Get student answers
        answers = data.get('answers', {})
        submission.answers_json = json.dumps(answers)
        submission.code_content = ''  # MCQ doesn't use code
        
        # Auto-grade multiple choice
        questions = json.loads(quiz.questions_json or '[]')
        correct_count = 0
        total_questions = len(questions)
        
        for idx, question in enumerate(questions):
            student_answer = answers.get(str(idx))
            correct_answer = question.get('correct_answer')
            
            # Convert correct_answer to index if it's a letter (A=0, B=1, C=2, D=3)
            if isinstance(correct_answer, str) and len(correct_answer) == 1:
                correct_answer_idx = ord(correct_answer.upper()) - ord('A')
            else:
                correct_answer_idx = correct_answer
            
            if student_answer is not None and student_answer == correct_answer_idx:
                correct_count += 1
        
        # Calculate score
        if total_questions > 0:
            submission.score = int((correct_count / total_questions) * quiz.max_score)
        else:
            submission.score = 0
        
        submission.status = 'graded'
        submission.graded_at = datetime.now()
    else:
        # Handle coding quiz
        code = data.get('code', '')
        submission.code_content = code
        submission.status = 'submitted'
    
    db.session.add(submission)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Quiz submitted successfully', 'score': submission.score})

@app.route('/teacher/quiz/<int:quiz_id>/delete', methods=['POST'])
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
        
        flash(f'Quiz "{quiz_title}" deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting quiz: {str(e)}', 'error')
    
    return redirect(url_for('view_course_quizzes', course_id=course_id))

@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404
