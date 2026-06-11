from flask import Blueprint, g
from flask import request

from app.utils.response import success_response, error_response
from app.services.auth_service import require_student
from app.services.review_service import get_available_courses, get_student_reviews
from app.storage.json_store import student_store

students_bp = Blueprint("students", __name__)


@students_bp.route("/<string:student_id>/available-courses", methods=["GET"])
@require_student
def available_courses(student_id: str):
    if g.user_id != student_id:
        return error_response("无权查看其他学生的可评课程", 403)

    student = student_store.get_by_id(student_id)
    if not student:
        return error_response("学生不存在", 404)

    courses = get_available_courses(student_id)
    return success_response({"courses": courses})


@students_bp.route("/<string:student_id>/reviews", methods=["GET"])
@require_student
def student_reviews(student_id: str):
    if g.user_id != student_id:
        return error_response("无权查看其他学生的评价记录", 403)

    student = student_store.get_by_id(student_id)
    if not student:
        return error_response("学生不存在", 404)

    reviews = get_student_reviews(student_id)
    return success_response({"reviews": reviews})
