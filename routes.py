from flask import session, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_user
from app import app, db
from replit_auth import require_login, require_role, make_replit_blueprint
from models import User, StudentProfile, TeacherProfile, Course, Enrollment, Assignment
from datetime import datetime

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
        
        if not title:
            flash('Course title is required.', 'error')
            return redirect(url_for('create_course'))
        
        course = Course()
        course.title = title
        course.description = description
        course.teacher_id = current_user.id
        db.session.add(course)
        db.session.commit()
        
        flash('Course created successfully!', 'success')
        return redirect(url_for('teacher_dashboard'))
    
    return redirect(url_for('teacher_dashboard'))

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
