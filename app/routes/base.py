from flask import Blueprint

from app.utils.response import success_response
from app.services.auth_service import require_auth
from app.storage.json_store import teacher_store, student_store

base_bp = Blueprint("base", __name__)


@base_bp.route("/teachers", methods=["GET"])
@require_auth
def list_teachers():
    teachers = teacher_store.get_all()
    result = []
    for teacher in teachers:
        result.append(
            {
                "teacherId": teacher.id,
                "name": teacher.name,
                "department": teacher.department,
            }
        )
    return success_response({"teachers": result})


@base_bp.route("/students", methods=["GET"])
@require_auth
def list_students():
    students = student_store.get_all()
    result = []
    for student in students:
        result.append(
            {
                "studentId": student.id,
                "studentNo": student.student_no,
                "name": student.name,
                "major": student.major,
                "grade": student.grade,
            }
        )
    return success_response({"students": result})
