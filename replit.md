# EduPortal

## Overview

EduPortal is a comprehensive Learning Management System (LMS) built with Flask that facilitates educational interactions between students and teachers. The application provides role-based access control, course management, assignment tracking, and user authentication through Replit's OAuth system. It features separate dashboards for students and teachers, allowing for tailored experiences based on user roles.

**Enhanced Programming Course Features:**
- Markdown-based content editor with live preview for course materials
- Reveal.js slide presentation system for engaging course delivery  
- PDF generation from course content using WeasyPrint for students
- File upload system for course slides (PDF/PPTX) with download access
- Content display selection: teachers choose between Markdown slides or uploaded files for student viewing
- Programming language and difficulty level categorization (now includes Scala)
- Estimated completion hours and prerequisite tracking
- Student enrollment system with course ID sharing and browsing options
- Teacher classroom management with student enrollment tracking and removal capabilities

**Form-Based Authentication System:**
- Custom user registration with username, email, and password
- All new registrations default to student role (teachers require manual promotion by administrators)
- Traditional login/logout functionality with session management  
- Role-specific profile creation during registration (StudentProfile/TeacherProfile)
- Database-driven user management with password hashing and validation
- Global CSRF protection via Flask-WTF for security

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Web Framework
- **Flask** serves as the primary web framework with SQLAlchemy ORM for database operations
- **MVC Pattern** with clear separation between models (database schemas), views (HTML templates), and controllers (routes)
- **Blueprint Architecture** for modular authentication handling through Replit OAuth

### Authentication & Authorization
- **Form-Based Authentication** with custom registration and login forms using Flask-WTF
- **Flask-Login** manages user sessions and login state
- **Role-Based Access Control** with decorator-based route protection (`@require_login`, `@require_role`)
- **Password Security** using Werkzeug's password hashing with secure defaults
- **Session Management** with persistent login sessions and mandatory SESSION_SECRET enforcement
- **User Registration** with validation for unique usernames/emails and password strength
- **Secure Registration** - All new users register as students; teacher role requires administrator promotion
- **Role-Specific Profiles** automatically created during registration with one-to-one user relationships

### Database Architecture
- **SQLAlchemy ORM** with declarative base model structure
- **User Model** serves as the central entity with role-based inheritance
- **Profile Models** extend user functionality with role-specific data (StudentProfile, TeacherProfile)
  - One-to-one relationships with unique user_id constraints
  - Prevents duplicate profiles per user
- **Enrollment Model** has unique constraint on (student_id, course_id) to prevent duplicate enrollments
- **OAuth Storage** handles token persistence linked to user sessions
- **Relationship Mapping** connects users to courses, assignments, and enrollments through foreign keys
- **Query Optimization** uses eager loading (joinedload) to eliminate N+1 query problems

### Frontend Architecture
- **Jinja2 Templates** with template inheritance using a base layout
- **Bootstrap 5** with dark theme for responsive UI components
- **Font Awesome Icons** for consistent iconography
- **Role-Specific Dashboards** providing tailored interfaces for students vs teachers
- **Progressive Enhancement** with JavaScript for interactive role selection

### Application Structure
- **Factory Pattern** for app creation with environment-based configuration
- **Proxy Fix Middleware** for proper HTTPS URL generation in production
- **Database Connection Pooling** with automatic reconnection and health checks
- **Logging Configuration** for debugging and monitoring

### Security Measures
- **CSRF Protection** globally enabled via Flask-WTF CSRFProtect
- **XSS Prevention** through Markdown sanitization using bleach with allowlist
- **File Upload Security** with 50MB size limit enforcement and extension validation
- **Session Secret Enforcement** - Application fails to start if SESSION_SECRET is not configured
- **Environment Variable Configuration** for sensitive data like database URLs and session secrets
- **Unique Constraints** on OAuth tokens to prevent session conflicts
- **Input Validation** on user registration with server-side role enforcement
- **Password Strength** minimum 6 characters with confirmation matching

## External Dependencies

### Authentication Services
- **Replit OAuth** - Primary authentication provider with user profile data
- **Flask-Dance** - OAuth client library for handling authorization flows

### Database
- **SQLAlchemy** - ORM and database abstraction layer
- **Database URL** - Environment-configured database connection (supports PostgreSQL, SQLite, etc.)

### Frontend Libraries
- **Bootstrap 5** - UI framework with dark theme variant
- **Font Awesome 6** - Icon library for interface elements
- **CDN Resources** - External hosting for CSS/JS libraries

### Python Packages
- **Flask-SQLAlchemy** - Database integration for Flask
- **Flask-Login** - User session management
- **Flask-WTF** - Form handling and CSRF protection
- **Bleach** - HTML sanitization for XSS prevention
- **Markdown** - Markdown to HTML conversion for course content
- **WeasyPrint** - PDF generation from HTML content
- **PyJWT** - JSON Web Token handling
- **Werkzeug** - WSGI utilities and proxy handling
- **OAuthLib** - OAuth protocol implementation

### Environment Configuration
- **SESSION_SECRET** - Flask session encryption key (required, application fails if not set)
- **DATABASE_URL** - Database connection string
- **Debug Mode** - Development vs production configuration

## Recent Changes (October 2025)

### Security Enhancements
- Removed arbitrary role switching functionality to prevent privilege escalation
- Added global CSRF protection for all POST requests
- Implemented XSS prevention through Markdown content sanitization
- Enforced mandatory SESSION_SECRET environment variable
- Restricted new user registration to student role only (teacher promotion requires admin)
- Enforced 50MB file upload size limit

### Database Improvements
- Fixed one-to-one relationships for StudentProfile and TeacherProfile
- Added unique constraint on Enrollment to prevent duplicate course enrollments
- Optimized queries with eager loading to eliminate N+1 query problems

### Bug Fixes
- Fixed template profile access (removed array indexing)
- Fixed CodeSubmission model field reference (code -> code_content)
- Fixed course_id variable scoping in quiz deletion

### UX Improvements
- Restored smooth animations and transitions in base template
- Improved responsive design for better user experience