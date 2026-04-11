import json

from app import db
from models import Course, Enrollment, Exam, StudentProfile, TeacherProfile, User


def _seed_course_with_exam():
    teacher = User(
        username="t1",
        email="t1@example.com",
        first_name="Tea",
        last_name="Cher",
        role="teacher",
    )
    teacher.set_password("secret12")
    db.session.add(teacher)
    db.session.flush()
    db.session.add(
        TeacherProfile(user_id=teacher.id, employee_id="EMP00000001", department="CS")
    )
    student = User(
        username="s1",
        email="s1@example.com",
        first_name="Stu",
        last_name="Dent",
        role="student",
    )
    student.set_password("secret12")
    db.session.add(student)
    db.session.flush()
    db.session.add(StudentProfile(user_id=student.id, student_id=f"STU{student.id:08d}", grade_level="9th Grade"))
    course = Course(
        title="Intro Python",
        description="d",
        content="# Hi\n",
        teacher_id=teacher.id,
        course_status="published",
    )
    db.session.add(course)
    db.session.flush()
    questions = [
        {
            "question": "2+2?",
            "options": [{"text": "3"}, {"text": "4"}, {"text": "5"}],
            "correct_answer": 1,
        }
    ]
    exam = Exam(
        title="Quiz 1",
        description="",
        course_id=course.id,
        questions_json=json.dumps(questions),
        max_score=100,
        is_active=True,
    )
    db.session.add(exam)
    db.session.commit()
    return student, teacher, course, exam


def test_enroll_post(client):
    with client.application.app_context():
        student, _teacher, course, _exam = _seed_course_with_exam()
        client.post(
            "/login",
            data={"username": student.username, "password": "secret12", "submit": "Sign In"},
        )
        r = client.post("/student/enroll", data={"course_id": str(course.id)}, follow_redirects=False)
        assert r.status_code in (302, 303)
        assert Enrollment.query.filter_by(student_id=student.id, course_id=course.id).first() is not None


def test_exam_submit_json(client):
    with client.application.app_context():
        student, _teacher, course, exam = _seed_course_with_exam()
        db.session.add(Enrollment(student_id=student.id, course_id=course.id))
        db.session.commit()
        student_username = student.username
        exam_id = exam.id

    client.post(
        "/login",
        data={"username": student_username, "password": "secret12", "submit": "Sign In"},
    )
    r = client.post(
        f"/student/exam/{exam_id}/submit",
        data=json.dumps({"answers": {"0": 1}}),
        content_type="application/json",
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data.get("success") is True
    assert "score" in data
