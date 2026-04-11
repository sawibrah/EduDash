# Gmail OAuth2 Authentication Module
# This module handles Google login using Flask-Dance

import os
from typing import Optional, Tuple

from flask import redirect, url_for, flash, session
from flask_babel import gettext
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import login_user

from app import db
from models import StudentProfile, User


def _unique_username(base: str) -> str:
    base = (base or "user").strip() or "user"
    username = base[:80] if len(base) > 80 else base
    if not User.query.filter_by(username=username).first():
        return username
    n = 1
    while True:
        suffix = f"_{n}"
        trimmed = base[: 80 - len(suffix)] + suffix
        if not User.query.filter_by(username=trimmed).first():
            return trimmed
        n += 1


def _split_google_name(full_name: Optional[str], fallback: str) -> Tuple[str, str]:
    if not full_name or not full_name.strip():
        return (fallback[:50] or "User", "-")
    parts = full_name.strip().split(None, 1)
    first = (parts[0] or fallback)[:50]
    last = (parts[1] if len(parts) > 1 else "-")[:50]
    return (first, last)


def init_google_oauth(app):
    """
    Initialize Google OAuth2 blueprint (optional).

    Environment variables:
    - GOOGLE_OAUTH_CLIENT_ID
    - GOOGLE_OAUTH_CLIENT_SECRET
    """
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        return None

    google_bp = make_google_blueprint(
        client_id=client_id,
        client_secret=client_secret,
        scopes=["profile", "email"],
        redirect_to="authorize_google",
    )

    # Avoid clashing with auth blueprint route ``/login``
    app.register_blueprint(google_bp, url_prefix="/oauth/google")

    app.add_url_rule(
        "/oauth/google/complete",
        endpoint="authorize_google",
        view_func=authorize_google,
        methods=["GET"],
    )

    return google_bp


def authorize_google():
    """Handle Google OAuth callback after Flask-Dance redirects here."""
    if not google.authorized:
        flash(gettext("Failed to log in with Google."), "error")
        return redirect(url_for("auth.login"))

    try:
        user_info = google.get("/oauth2/v1/userinfo").json()
        email = user_info.get("email")
        name = user_info.get("name")

        if not email:
            flash(gettext("Could not get email from Google account."), "error")
            return redirect(url_for("auth.login"))

        user = User.query.filter_by(email=email).first()
        email_local = (email.split("@", 1)[0] if "@" in email else email).strip() or "user"

        if not user:
            first_name, last_name = _split_google_name(name, email_local)
            username = _unique_username(email_local)
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role="student",
            )
            user.set_password("google-oauth")
            db.session.add(user)
            db.session.flush()
            db.session.add(
                StudentProfile(
                    user_id=user.id,
                    student_id=f"STU{user.id:08d}",
                    grade_level="9th Grade",
                )
            )
            db.session.commit()
            flash(gettext("Welcome! Account created for %(email)s", email=email), "success")
        else:
            display = user.get_full_name()
            flash(gettext("Welcome back, %(name)s!", name=display), "success")

        login_user(user)

        next_url = session.pop("next_url", None)
        if next_url:
            return redirect(next_url)
        return redirect(url_for("main.index"))

    except Exception as e:
        flash(gettext("Error during Google authentication: %(err)s", err=str(e)), "error")
        return redirect(url_for("auth.login"))


def google_login_url():
    """Return Google login URL for templates, or None if already authorized."""
    if not google.authorized:
        return url_for("google.login")
    return None
