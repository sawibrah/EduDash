# EduPortal

## Overview

EduPortal is a comprehensive Learning Management System (LMS) built with Flask that facilitates educational interactions between students and teachers. The application provides role-based access control, course management, assignment tracking, and user authentication through Replit's OAuth system. It features separate dashboards for students and teachers, allowing for tailored experiences based on user roles.

**Enhanced Programming Course Features:**
- Markdown-based content editor with live preview for course materials
- Reveal.js slide presentation system for engaging course delivery  
- PDF generation from course content using WeasyPrint for students
- Programming language and difficulty level categorization (now includes Scala)
- Estimated completion hours and prerequisite tracking

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Web Framework
- **Flask** serves as the primary web framework with SQLAlchemy ORM for database operations
- **MVC Pattern** with clear separation between models (database schemas), views (HTML templates), and controllers (routes)
- **Blueprint Architecture** for modular authentication handling through Replit OAuth

### Authentication & Authorization
- **Replit OAuth Integration** provides seamless single sign-on authentication
- **Flask-Login** manages user sessions and login state
- **Role-Based Access Control** with decorator-based route protection (`@require_login`, `@require_role`)
- **JWT Token Handling** for secure OAuth token management
- **Session Management** with browser session key tracking for multi-device support

### Database Architecture
- **SQLAlchemy ORM** with declarative base model structure
- **User Model** serves as the central entity with role-based inheritance
- **Profile Models** extend user functionality with role-specific data (StudentProfile, TeacherProfile)
- **OAuth Storage** handles token persistence linked to user sessions
- **Relationship Mapping** connects users to courses, assignments, and enrollments through foreign keys

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
- **CSRF Protection** through Flask's secret key management
- **Environment Variable Configuration** for sensitive data like database URLs and session secrets
- **Unique Constraints** on OAuth tokens to prevent session conflicts
- **Input Validation** on role selection and user registration

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
- **PyJWT** - JSON Web Token handling
- **Werkzeug** - WSGI utilities and proxy handling
- **OAuthLib** - OAuth protocol implementation

### Environment Configuration
- **SESSION_SECRET** - Flask session encryption key
- **DATABASE_URL** - Database connection string
- **Debug Mode** - Development vs production configuration