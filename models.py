from datetime import datetime
from app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint

# User model updated for form-based authentication
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'teacher'
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def is_student(self):
        return self.role == 'student'
    
    def is_teacher(self):
        return self.role == 'teacher'

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
# Keep OAuth table but update for integer foreign keys (legacy support)
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

# Student-specific data
class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False, unique=True)
    student_id = db.Column(db.String, unique=True, nullable=True)
    grade_level = db.Column(db.String, nullable=True)
    enrollment_date = db.Column(db.DateTime, default=datetime.now)
    user = db.relationship(User, backref=db.backref('student_profile', uselist=False))

# Teacher-specific data
class TeacherProfile(db.Model):
    __tablename__ = 'teacher_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False, unique=True)
    employee_id = db.Column(db.String, unique=True, nullable=True)
    department = db.Column(db.String, nullable=True)
    hire_date = db.Column(db.DateTime, default=datetime.now)
    user = db.relationship(User, backref=db.backref('teacher_profile', uselist=False))

# Courses (managed by teachers)
class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=True)  # Markdown content
    difficulty_level = db.Column(db.String(50), nullable=True)  # Beginner, Intermediate, Advanced
    programming_language = db.Column(db.String(50), nullable=True)  # Python, JavaScript, etc.
    estimated_hours = db.Column(db.Integer, nullable=True)  # Course duration in hours
    prerequisites = db.Column(db.Text, nullable=True)  # Prerequisites as text
    learning_objectives = db.Column(db.Text, nullable=True)  # What students will learn
    course_status = db.Column(db.String(20), default='draft')  # draft, published, archived
    pdf_generated = db.Column(db.Boolean, default=False)
    pdf_path = db.Column(db.String(255), nullable=True)  # Path to generated PDF
    
    # File upload fields
    uploaded_file_path = db.Column(db.String(255), nullable=True)  # Path to uploaded slide file
    uploaded_file_type = db.Column(db.String(10), nullable=True)  # 'pdf' or 'pptx'
    uploaded_file_name = db.Column(db.String(255), nullable=True)  # Original filename
    content_display_type = db.Column(db.String(20), default='markdown', nullable=False)  # 'markdown' or 'uploaded_file'
    
    teacher_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    teacher = db.relationship(User, backref='courses')

# Student enrollments
class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='unique_student_course_enrollment'),
    )
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey(Course.id), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.now)
    student = db.relationship(User, backref='enrollments')
    course = db.relationship(Course, backref='enrollments')

# Assignments
class Assignment(db.Model):
    __tablename__ = 'assignments'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey(Course.id), nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    course = db.relationship(Course, backref='assignments')

# Programming Quizzes with Code Editor and Multiple Choice
class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey(Course.id), nullable=False)
    quiz_type = db.Column(db.String(20), default='multiple_choice', nullable=False)  # 'multiple_choice' or 'coding'
    
    # Multiple Choice fields
    questions_json = db.Column(db.Text, nullable=True)  # JSON string of questions and answers
    
    # Coding quiz fields
    programming_language = db.Column(db.String(50), nullable=True)
    starter_code = db.Column(db.Text, default='')
    expected_output = db.Column(db.Text, default='')
    instructions = db.Column(db.Text)
    
    # Common fields
    max_score = db.Column(db.Integer, default=100)
    time_limit = db.Column(db.Integer, default=60)  # minutes
    due_date = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    course = db.relationship(Course, backref='quizzes')

# Quiz Submissions (both code and multiple choice)
class CodeSubmission(db.Model):
    __tablename__ = 'code_submissions'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey(Quiz.id), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    
    # Code submission fields
    code_content = db.Column(db.Text, nullable=True)
    language = db.Column(db.String(50))
    output = db.Column(db.Text, default='')
    execution_time = db.Column(db.Float)
    memory_usage = db.Column(db.Integer)
    
    # Multiple choice submission fields
    answers_json = db.Column(db.Text, nullable=True)  # JSON string of student answers
    
    # Common fields
    status = db.Column(db.String(20), default='submitted')  # submitted, graded, reviewed
    score = db.Column(db.Integer)
    feedback = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.now)
    graded_at = db.Column(db.DateTime)
    
    quiz = db.relationship(Quiz, backref='submissions')
    student = db.relationship(User, backref='code_submissions')
