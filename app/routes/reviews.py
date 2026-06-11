from flask import Blueprint, g, request

from app.utils.response import success_response, error_response
from app.services.auth_service import require_student
from app.services.review_service import (
    validate_review_submission,
    create_review,
)

reviews_bp = Blueprint("reviews", __name__)


@reviews_bp.route("", methods=["POST"])
@require_student
def submit_review():
    data = request.get_json()
    if not data:
        return error_response("请求体不能为空", 400)

    required_fields = [
        "student_id",
        "course_id",
        "semester",
        "content_score",
        "difficulty_score",
        "gain_score",
        "comment",
    ]
    for field in required_fields:
        if field not in data:
            return error_response(f"缺少必填字段: {field}", 400)

    student_id = data["student_id"]
    if g.user_id != student_id:
        return error_response("无权替其他学生提交评价", 403)

    validation = validate_review_submission(
        student_id=student_id,
        course_id=data["course_id"],
        semester=data["semester"],
        content_score=data["content_score"],
        difficulty_score=data["difficulty_score"],
        gain_score=data["gain_score"],
        comment=data["comment"],
    )

    if not validation.valid:
        return error_response(validation.error_msg, validation.error_code)

    review = create_review(
        student_id=student_id,
        course_id=data["course_id"],
        semester=data["semester"],
        content_score=data["content_score"],
        difficulty_score=data["difficulty_score"],
        gain_score=data["gain_score"],
        comment=data["comment"],
    )

    return success_response(
        {
            "reviewId": review.id,
            "sensitiveFlag": review.sensitive_flag,
        },
        "评价提交成功",
    )
