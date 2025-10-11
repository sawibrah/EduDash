# EduPortal

## Overview
EduPortal is a comprehensive Flask-based Learning Management System (LMS) designed to facilitate educational interactions with role-based access for students and teachers. It features course management, assignment tracking, and user authentication via Replit's OAuth. The platform offers tailored dashboards for different roles. Key capabilities include enhanced programming course features with rich content support (Markdown, Reveal.js, PDF generation), a robust MCQ-based exam system with automatic grading and rich content, and a similar rich-content quiz system. The system also includes a custom form-based authentication system with secure user registration, password management, and a three-tier role system (Admin, Teacher, Student). The business vision is to provide an intuitive and secure educational platform with advanced content delivery and assessment tools.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### Web Framework
- **Flask** with SQLAlchemy ORM, adhering to an **MVC Pattern**.
- **Blueprint Architecture** for modularity.

### Authentication & Authorization
- **Form-Based Authentication** using Flask-WTF and Flask-Login.
- **Three-Tier Role System** (Admin, Teacher, Student) with decorator-based protection.
- **Password Security** via Werkzeug's hashing and forced password change mechanism.
- **Replit OAuth** for external authentication, managed by Flask-Dance.
- **Role-Specific Profiles** and secure registration processes.

### Database Architecture
- **SQLAlchemy ORM** with declarative base models.
- **User, Profile (Student/Teacher), Enrollment Models** with one-to-one and unique constraints.
- **OAuth Storage** for token persistence.
- **Relationship Mapping** using foreign keys and eager loading for query optimization.

### Frontend Architecture
- **Jinja2 Templates** with inheritance.
- **Bootstrap 5 (dark theme)** and **Font Awesome Icons** for UI.
- **Role-Specific Dashboards** and responsive design.

### Application Structure
- **Factory Pattern** for app creation.
- **Proxy Fix Middleware**, database connection pooling, and logging.

### Security Measures
- **Global CSRF Protection** (Flask-WTF).
- **XSS Prevention** via Bleach for Markdown sanitization.
- **File Upload Security** with size/extension validation.
- **Mandatory SESSION_SECRET** and environment variable configuration.
- **Input Validation** and strong password enforcement.

### Feature Specifications
- **Programming Course Features**: Markdown editor, Reveal.js integration, PDF generation, file uploads, content display toggling, language/difficulty categorization, estimated completion hours, prerequisite tracking, student enrollment, teacher classroom management.
- **Exam System**: MCQ format, rich content (images, code blocks with syntax highlighting), automatic grading, optional explanations, timed exams, due date enforcement, submission tracking, progress indicator.
- **Quiz System**: MCQ format, rich content, syntax highlighting, question template builder, automatic grading, optional explanations, timed quizzes, due date support, student progress tracking, activation system.
- **Form-Based Authentication**: Custom registration, login/logout, session management, role-specific profile creation, password hashing, global CSRF protection, forced password change on first login/reset.

## External Dependencies

### Authentication Services
- **Replit OAuth**
- **Flask-Dance**

### Database
- **SQLAlchemy** (ORM)
- **Environment-configured Database URL** (e.g., PostgreSQL, SQLite)

### Frontend Libraries
- **Bootstrap 5**
- **Font Awesome 6**
- **CDN Resources** for CSS/JS libraries

### Python Packages
- **Flask-SQLAlchemy**
- **Flask-Login**
- **Flask-WTF**
- **Bleach**
- **Markdown**
- **WeasyPrint**
- **PyJWT**
- **Werkzeug**
- **OAuthLib**

### Environment Configuration
- **SESSION_SECRET** (required)
- **DATABASE_URL**
- **Debug Mode**