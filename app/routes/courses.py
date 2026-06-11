from flask import Blueprint

from app.utils.response import success_response
from app.services.auth_service import require_auth
from app.storage.json_store import course_store, teacher_store

courses_bp = Blueprint("courses", __name__)


@courses_bp.route("", methods=["GET"])
@require_auth
def list_courses():
    courses = course_store.get_all()
    result = []
    for course in courses:
        teacher = teacher_store.get_by_id(course.teacher_id)
        result.append(
            {
                "courseId": course.id,
                "courseName": course.name,
                "teacherId": course.teacher_id,
                "teacherName": teacher.name if teacher else "",
                "semester": course.semester,
                "credits": course.credits,
                "status": course.status,
            }
        )
    return success_response({"courses": result})
