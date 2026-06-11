import uuid
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass
from typing import Self

from app.config import Config
from app.models.dataclasses import (
    Course,
    Enrollment,
    Review,
    Semester,
    SemesterStatus,
)
from app.storage.json_store import (
    course_store,
    enrollment_store,
    review_store,
    semester_store,
    student_store,
)
from app.censor.censor import word_censor


@dataclass
class ValidationResult:
    valid: bool
    error_msg: str | None = None
    error_code: int = 400


@dataclass
class CourseSummary:
    course_id: str
    course_name: str
    semester: str
    total_reviews: int
    content_avg: float
    difficulty_avg: float
    gain_avg: float
    score_distribution: dict[int, int]

    def to_dict(self) -> dict:
        return {
            "courseId": self.course_id,
            "courseName": self.course_name,
            "semester": self.semester,
            "totalReviews": self.total_reviews,
            "contentAvg": round(self.content_avg, 2),
            "difficultyAvg": round(self.difficulty_avg, 2),
            "gainAvg": round(self.gain_avg, 2),
            "scoreDistribution": self.score_distribution,
        }


@dataclass
class AdminStats:
    total_reviews: int
    total_courses_evaluated: int
    total_students_reviewed: int
    sensitive_hit_rate: float
    avg_score_overall: float
    top_reviewed_courses: list[dict[str, str | int]]

    def to_dict(self) -> dict:
        return {
            "totalReviews": self.total_reviews,
            "totalCoursesEvaluated": self.total_courses_evaluated,
            "totalStudentsReviewed": self.total_students_reviewed,
            "sensitiveHitRate": round(self.sensitive_hit_rate, 4),
            "avgScoreOverall": round(self.avg_score_overall, 2),
            "topReviewedCourses": self.top_reviewed_courses,
        }


def _parse_semester(semester_str: str) -> tuple[int, int]:
    parts = semester_str.split("-")
    year = int(parts[0])
    season = parts[1]
    season_order = 1 if season == "spring" else 2
    return year, season_order


def _semesters_apart(current: str, past: str) -> int:
    curr_year, curr_season = _parse_semester(current)
    past_year, past_season = _parse_semester(past)
    return (curr_year - past_year) * 2 + (curr_season - past_season)


def _get_current_semester() -> str:
    semesters = semester_store.get_all()
    if not semesters:
        return ""
    semesters_sorted = sorted(semesters, key=lambda s: s.id, reverse=True)
    return semesters_sorted[0].id


def validate_review_submission(
    student_id: str,
    course_id: str,
    semester: str,
    content_score: int,
    difficulty_score: int,
    gain_score: int,
    comment: str,
) -> ValidationResult:
    student = student_store.get_by_id(student_id)
    if not student:
        return ValidationResult(False, "学生不存在", 404)

    course = course_store.get_by_id(course_id)
    if not course:
        return ValidationResult(False, "课程不存在", 404)

    if course.semester != semester:
        return ValidationResult(False, "课程学期不匹配", 400)

    enrollment = enrollment_store.filter(
        student_id=student_id, course_id=course_id, semester=semester
    )
    if not enrollment:
        return ValidationResult(False, "未选修该课程", 422)

    if not enrollment[0].is_finished:
        return ValidationResult(False, "课程未结课，暂不可评价", 422)

    existing = review_store.filter(
        student_id=student_id, course_id=course_id, semester=semester
    )
    if existing:
        return ValidationResult(False, "该课程已评价过，不可重复评价", 409)

    current_semester = _get_current_semester()
    if current_semester:
        semesters_passed = _semesters_apart(current_semester, semester)
        if semesters_passed > Config.MAX_SEMESTERS_PAST:
            return ValidationResult(False, "该课程结课已超过2学期，不可再评价", 422)

    for score_name, score in [
        ("内容质量", content_score),
        ("难度感受", difficulty_score),
        ("收获程度", gain_score),
    ]:
        if not isinstance(score, int) or score < 1 or score > 5:
            return ValidationResult(False, f"{score_name}评分必须是1-5的整数", 400)

    if not isinstance(comment, str):
        return ValidationResult(False, "评语文本必须是字符串", 400)

    if len(comment) < Config.MIN_REVIEW_LENGTH:
        return ValidationResult(False, f"评语文本长度至少{Config.MIN_REVIEW_LENGTH}字", 400)

    if len(comment) > Config.MAX_REVIEW_LENGTH:
        return ValidationResult(False, f"评语文本长度不能超过{Config.MAX_REVIEW_LENGTH}字", 400)

    return ValidationResult(True)


def create_review(
    student_id: str,
    course_id: str,
    semester: str,
    content_score: int,
    difficulty_score: int,
    gain_score: int,
    comment: str,
) -> Review:
    censor_result = word_censor.censor(comment)

    review = Review(
        id=str(uuid.uuid4()),
        student_id=student_id,
        course_id=course_id,
        semester=semester,
        content_score=content_score,
        difficulty_score=difficulty_score,
        gain_score=gain_score,
        comment=censor_result.text,
        submit_time=datetime.utcnow().isoformat(),
        sensitive_flag=censor_result.has_sensitive,
    )

    review_store.add(review)
    return review


def get_available_courses(student_id: str) -> list[dict]:
    enrollments = enrollment_store.filter(student_id=student_id, is_finished=True)
    reviewed_courses = []
    current_semester = _get_current_semester()

    for enrollment in enrollments:
        course = course_store.get_by_id(enrollment.course_id)
        if not course:
            continue

        if current_semester:
            semesters_passed = _semesters_apart(current_semester, course.semester)
            if semesters_passed > Config.MAX_SEMESTERS_PAST:
                continue

        existing = review_store.filter(
            student_id=student_id, course_id=enrollment.course_id, semester=course.semester
        )
        if existing:
            continue

        reviewed_courses.append(
            {
                "courseId": course.id,
                "courseName": course.name,
                "semester": course.semester,
                "credits": course.credits,
                "teacherId": course.teacher_id,
            }
        )

    return reviewed_courses


def get_student_reviews(student_id: str) -> list[dict]:
    reviews = review_store.filter(student_id=student_id)
    result = []
    for review in reviews:
        course = course_store.get_by_id(review.course_id)
        result.append(
            {
                "reviewId": review.id,
                "courseId": review.course_id,
                "courseName": course.name if course else "",
                "semester": review.semester,
                "contentScore": review.content_score,
                "difficultyScore": review.difficulty_score,
                "gainScore": review.gain_score,
                "comment": review.comment,
                "submitTime": review.submit_time,
                "sensitiveFlag": review.sensitive_flag,
            }
        )
    return result


def get_teacher_courses(teacher_id: str) -> list[dict]:
    courses = course_store.filter(teacher_id=teacher_id)
    result = []
    for course in courses:
        reviews = review_store.filter(course_id=course.id)
        result.append(
            {
                "courseId": course.id,
                "courseName": course.name,
                "semester": course.semester,
                "credits": course.credits,
                "status": course.status,
                "reviewCount": len(reviews),
            }
        )
    return result


def get_course_summary(teacher_id: str, course_id: str) -> CourseSummary | None:
    course = course_store.get_by_id(course_id)
    if not course or course.teacher_id != teacher_id:
        return None

    reviews = review_store.filter(course_id=course_id)
    if not reviews:
        return CourseSummary(
            course_id=course.id,
            course_name=course.name,
            semester=course.semester,
            total_reviews=0,
            content_avg=0.0,
            difficulty_avg=0.0,
            gain_avg=0.0,
            score_distribution={1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        )

    total_content = sum(r.content_score for r in reviews)
    total_difficulty = sum(r.difficulty_score for r in reviews)
    total_gain = sum(r.gain_score for r in reviews)
    count = len(reviews)

    score_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in reviews:
        avg_score = (r.content_score + r.difficulty_score + r.gain_score) / 3
        bucket = min(5, max(1, round(avg_score)))
        score_dist[bucket] += 1

    return CourseSummary(
        course_id=course.id,
        course_name=course.name,
        semester=course.semester,
        total_reviews=count,
        content_avg=total_content / count,
        difficulty_avg=total_difficulty / count,
        gain_avg=total_gain / count,
        score_distribution=score_dist,
    )


def get_admin_stats() -> AdminStats:
    all_reviews = review_store.get_all()
    total_reviews = len(all_reviews)

    course_review_counts: dict[str, int] = defaultdict(int)
    student_ids: set[str] = set()
    sensitive_count = 0
    total_score = 0.0

    for review in all_reviews:
        course_review_counts[review.course_id] += 1
        student_ids.add(review.student_id)
        if review.sensitive_flag:
            sensitive_count += 1
        total_score += (review.content_score + review.difficulty_score + review.gain_score) / 3

    total_courses = len(course_review_counts)
    total_students = len(student_ids)

    avg_score = total_score / total_reviews if total_reviews > 0 else 0.0
    sensitive_rate = sensitive_count / total_reviews if total_reviews > 0 else 0.0

    sorted_courses = sorted(
        course_review_counts.items(), key=lambda x: x[1], reverse=True
    )[:10]
    top_courses = [
        {"courseId": cid, "count": cnt} for cid, cnt in sorted_courses
    ]

    return AdminStats(
        total_reviews=total_reviews,
        total_courses_evaluated=total_courses,
        total_students_reviewed=total_students,
        sensitive_hit_rate=sensitive_rate,
        avg_score_overall=avg_score,
        top_reviewed_courses=top_courses,
    )


def close_semester(semester_id: str) -> bool:
    semester = semester_store.get_by_id(semester_id)
    if not semester:
        return False

    semester.status = SemesterStatus.CLOSED
    semester_store.update(semester)

    courses = course_store.filter(semester=semester_id)
    for course in courses:
        course.status = "closed"
        course_store.update(course)

    enrollments = enrollment_store.filter(semester=semester_id)
    for enrollment in enrollments:
        enrollment.is_finished = True
        enrollment_store.update(enrollment)

    return True
