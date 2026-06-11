from dataclasses import dataclass, field, asdict
from typing import Self, Optional
from datetime import datetime
from enum import Enum


class SemesterStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class Role(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


@dataclass
class Course:
    id: str
    name: str
    teacher_id: str
    semester: str
    credits: int
    status: str = "active"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(
            id=data["id"],
            name=data["name"],
            teacher_id=data["teacher_id"],
            semester=data["semester"],
            credits=data["credits"],
            status=data.get("status", "active"),
        )


@dataclass
class Enrollment:
    id: str
    student_id: str
    course_id: str
    semester: str
    enroll_time: str
    is_finished: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(
            id=data["id"],
            student_id=data["student_id"],
            course_id=data["course_id"],
            semester=data["semester"],
            enroll_time=data["enroll_time"],
            is_finished=data.get("is_finished", False),
        )


@dataclass
class Teacher:
    id: str
    name: str
    department: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(
            id=data["id"],
            name=data["name"],
            department=data["department"],
        )


@dataclass
class Student:
    id: str
    student_no: str
    name: str
    major: str
    grade: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(
            id=data["id"],
            student_no=data["student_no"],
            name=data["name"],
            major=data["major"],
            grade=data["grade"],
        )


@dataclass
class Review:
    id: str
    student_id: str
    course_id: str
    semester: str
    content_score: int
    difficulty_score: int
    gain_score: int
    comment: str
    submit_time: str
    sensitive_flag: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(
            id=data["id"],
            student_id=data["student_id"],
            course_id=data["course_id"],
            semester=data["semester"],
            content_score=data["content_score"],
            difficulty_score=data["difficulty_score"],
            gain_score=data["gain_score"],
            comment=data["comment"],
            submit_time=data["submit_time"],
            sensitive_flag=data.get("sensitive_flag", False),
        )


@dataclass
class Semester:
    id: str
    start_date: str
    end_date: str
    status: SemesterStatus = SemesterStatus.ACTIVE

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        status = data.get("status", "active")
        match status:
            case "closed":
                status_enum = SemesterStatus.CLOSED
            case "archived":
                status_enum = SemesterStatus.ARCHIVED
            case _:
                status_enum = SemesterStatus.ACTIVE
        return cls(
            id=data["id"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            status=status_enum,
        )
