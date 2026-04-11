# -*- coding: utf-8 -*-
"""One-off: update templates to blueprint-qualified url_for names. Run from repo root."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPLACEMENTS = [
    ("url_for('admin_toggle_teacher_capability'", "url_for('admin.admin_toggle_teacher_capability'"),
    ("url_for('admin_toggle_course_status'", "url_for('admin.admin_toggle_course_status'"),
    ("url_for('admin_reset_password'", "url_for('admin.admin_reset_password'"),
    ("url_for('admin_delete_user'", "url_for('admin.admin_delete_user'"),
    ("url_for('admin_create_user'", "url_for('admin.admin_create_user'"),
    ("url_for('admin_dashboard'", "url_for('admin.admin_dashboard'"),
    ("url_for('admin_users'", "url_for('admin.admin_users'"),
    ("url_for('admin_courses'", "url_for('admin.admin_courses'"),
    ("url_for('promote_user'", "url_for('admin.promote_user'"),
    ("url_for('teacher_dashboard'", "url_for('teacher.teacher_dashboard'"),
    ("url_for('student_dashboard'", "url_for('student.student_dashboard'"),
    ("url_for('student_download_course_pdf'", "url_for('student.student_download_course_pdf'"),
    ("url_for('student_take_exam'", "url_for('student.student_take_exam'"),
    ("url_for('enroll_course'", "url_for('student.enroll_course'"),
    ("url_for('take_quiz'", "url_for('student.take_quiz'"),
    ("url_for('view_course_quizzes'", "url_for('teacher.view_course_quizzes'"),
    ("url_for('view_quiz_submissions'", "url_for('teacher.view_quiz_submissions'"),
    ("url_for('reset_quiz_submissions'", "url_for('teacher.reset_quiz_submissions'"),
    ("url_for('create_mcq_quiz'", "url_for('teacher.create_mcq_quiz'"),
    ("url_for('edit_mcq_quiz'", "url_for('teacher.edit_mcq_quiz'"),
    ("url_for('create_quiz'", "url_for('teacher.create_quiz'"),
    ("url_for('view_course_exams'", "url_for('teacher.view_course_exams'"),
    ("url_for('show_create_exam'", "url_for('teacher.show_create_exam'"),
    ("url_for('show_edit_exam'", "url_for('teacher.show_edit_exam'"),
    ("url_for('update_exam'", "url_for('teacher.update_exam'"),
    ("url_for('create_exam'", "url_for('teacher.create_exam'"),
    ("url_for('generate_course_pdf'", "url_for('teacher.generate_course_pdf'"),
    ("url_for('download_course_pdf'", "url_for('teacher.download_course_pdf'"),
    ("url_for('view_course_students'", "url_for('teacher.view_course_students'"),
    ("url_for('remove_student'", "url_for('teacher.remove_student'"),
    ("url_for('create_course'", "url_for('teacher.create_course'"),
    ("url_for('edit_course'", "url_for('teacher.edit_course'"),
    ("url_for('view_course'", "url_for('teacher.view_course'"),
    ("url_for('download_course_slides'", "url_for('courses.download_course_slides'"),
    ("url_for('view_course_file'", "url_for('courses.view_course_file'"),
    ("url_for('view_course_slides'", "url_for('courses.view_course_slides'"),
    ("url_for('browse_courses'", "url_for('main.browse_courses'"),
    ("url_for('test_login'", "url_for('main.test_login'"),
    ("url_for('set_language'", "url_for('main.set_language'"),
    ("url_for('change_password'", "url_for('auth.change_password'"),
    ("url_for('register'", "url_for('auth.register'"),
    ("url_for('logout'", "url_for('auth.logout'"),
    ("url_for('login'", "url_for('auth.login'"),
    ("url_for('index'", "url_for('main.index'"),
]


def main():
    for path in ROOT.joinpath("templates").rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        orig = text
        for old, new in REPLACEMENTS:
            text = text.replace(old, new)
        if text != orig:
            path.write_text(text, encoding="utf-8")
            print("patched", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
