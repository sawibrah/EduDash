"""Register Flask blueprints and app-level hooks."""
from flask import flash, redirect, render_template, request, session, url_for
from flask_babel import gettext
from flask_login import current_user


def register_blueprints(app):
    from blueprints.admin_routes import admin_bp
    from blueprints.api_routes import api_bp
    from blueprints.auth_routes import auth_bp
    from blueprints.courses_routes import courses_bp
    from blueprints.main_routes import main_bp
    from blueprints.student_routes import student_bp
    from blueprints.teacher_routes import teacher_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)

    @app.before_request
    def make_session_permanent():
        session.permanent = True

    @app.before_request
    def check_password_change_required():
        exempt = {"auth.change_password", "auth.logout", "static"}
        if current_user.is_authenticated and current_user.password_change_required:
            if request.endpoint not in exempt:
                flash(gettext("You must change your password before continuing."), "warning")
                return redirect(url_for("auth.change_password"))

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404
