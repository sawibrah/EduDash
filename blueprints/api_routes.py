"""JSON API blueprint."""
from flask import Blueprint, jsonify
from flask_login import current_user
from sqlalchemy.orm import joinedload

from app import csrf
from auth import require_role
from models import Course, Enrollment

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/available-courses")
@require_role("student")
@csrf.exempt
def available_courses_api():
    enrolled_course_ids = [e.course_id for e in Enrollment.query.filter_by(student_id=current_user.id).all()]
    available_courses = (
        Course.query.options(joinedload(Course.teacher))
        .filter(Course.course_status == "published", ~Course.id.in_(enrolled_course_ids))
        .all()
    )
    courses_data = []
    for course in available_courses:
        courses_data.append(
            {
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "programming_language": course.programming_language,
                "difficulty_level": course.difficulty_level,
                "estimated_hours": course.estimated_hours,
                "teacher_name": (
                    f"{course.teacher.first_name} {course.teacher.last_name}" if course.teacher else "Unknown"
                ),
            }
        )
    return jsonify(courses_data)
