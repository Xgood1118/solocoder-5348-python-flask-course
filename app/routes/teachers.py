from flask import Blueprint, g

from app.utils.response import success_response, error_response
from app.services.auth_service import require_teacher
from app.services.review_service import get_teacher_courses, get_course_summary
from app.storage.json_store import teacher_store

teachers_bp = Blueprint("teachers", __name__)


@teachers_bp.route("/<string:teacher_id>/courses", methods=["GET"])
@require_teacher
def teacher_courses(teacher_id: str):
    if g.user_id != teacher_id:
        return error_response("无权查看其他教师的课程", 403)

    teacher = teacher_store.get_by_id(teacher_id)
    if not teacher:
        return error_response("教师不存在", 404)

    courses = get_teacher_courses(teacher_id)
    return success_response({"courses": courses})


@teachers_bp.route("/<string:teacher_id>/courses/<string:course_id>/summary", methods=["GET"])
@require_teacher
def course_summary(teacher_id: str, course_id: str):
    if g.user_id != teacher_id:
        return error_response("无权查看其他教师的课程汇总", 403)

    summary = get_course_summary(teacher_id, course_id)
    if not summary:
        return error_response("课程不存在或不属于该教师", 404)

    return success_response(summary.to_dict())
