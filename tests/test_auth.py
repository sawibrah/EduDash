from app import db
from models import StudentProfile, User


def test_login_page_ok(client):
    r = client.get("/login")
    assert r.status_code == 200


def test_login_success_redirects_student_dashboard(client):
    with client.application.app_context():
        u = User(
            username="logintest",
            email="logintest@example.com",
            first_name="L",
            last_name="T",
            role="student",
        )
        u.set_password("secret12")
        db.session.add(u)
        db.session.flush()
        db.session.add(
            StudentProfile(user_id=u.id, student_id=f"STU{u.id:08d}", grade_level="9th Grade")
        )
        db.session.commit()

    r = client.post(
        "/login",
        data={"username": "logintest", "password": "secret12", "submit": "Sign In"},
        follow_redirects=False,
    )
    assert r.status_code in (302, 303)
    assert "/student/dashboard" in r.headers.get("Location", "")
