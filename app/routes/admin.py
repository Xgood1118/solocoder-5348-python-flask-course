from flask import Blueprint, request

from app.utils.response import success_response, error_response
from app.services.auth_service import (
    require_admin,
    verify_admin,
    generate_admin_token,
)
from app.services.review_service import get_admin_stats, close_semester
from app.censor.censor import word_censor
from app.storage.json_store import review_store, semester_store

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/login", methods=["POST"])
def admin_login():
    data = request.get_json()
    if not data:
        return error_response("请求体不能为空", 400)

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return error_response("用户名和密码不能为空", 400)

    if not verify_admin(username, password):
        return error_response("用户名或密码错误", 401)

    token = generate_admin_token(username)
    return success_response({"token": token}, "登录成功")


@admin_bp.route("/reviews", methods=["GET"])
@require_admin
def list_reviews():
    sensitive = request.args.get("sensitive", "").lower() == "true"

    reviews = review_store.get_all()
    if sensitive:
        reviews = [r for r in reviews if r.sensitive_flag]

    result = []
    for review in reviews:
        result.append(
            {
                "reviewId": review.id,
                "studentId": review.student_id,
                "courseId": review.course_id,
                "semester": review.semester,
                "contentScore": review.content_score,
                "difficultyScore": review.difficulty_score,
                "gainScore": review.gain_score,
                "comment": review.comment,
                "submitTime": review.submit_time,
                "sensitiveFlag": review.sensitive_flag,
            }
        )

    return success_response({"reviews": result})


@admin_bp.route("/stats", methods=["GET"])
@require_admin
def admin_stats():
    stats = get_admin_stats()
    return success_response(stats.to_dict())


@admin_bp.route("/semesters/<string:semester_id>/close", methods=["POST"])
@require_admin
def close_semester_endpoint(semester_id: str):
    success = close_semester(semester_id)
    if not success:
        return error_response("学期不存在", 404)
    return success_response(None, "学期结课操作成功")


@admin_bp.route("/censor-words", methods=["POST"])
@require_admin
def update_censor_words():
    data = request.get_json()
    if not data or "words" not in data:
        return error_response("缺少 words 字段", 400)

    words = data["words"]
    if not isinstance(words, list):
        return error_response("words 必须是字符串数组", 400)

    word_censor.reload_words(words)
    return success_response({"count": len(word_censor.get_words())}, "敏感词库更新成功")


@admin_bp.route("/censor-words", methods=["GET"])
@require_admin
def get_censor_words():
    words = word_censor.get_words()
    return success_response({"words": words})


@admin_bp.route("/semesters", methods=["GET"])
@require_admin
def list_semesters():
    semesters = semester_store.get_all()
    result = []
    for semester in semesters:
        result.append(semester.to_dict())
    return success_response({"semesters": result})
