import os
from dataclasses import dataclass


@dataclass
class Config:
    PORT: int = int(os.getenv("PORT", "8080"))
    ADMIN_USER: str = os.getenv("ADMIN_USER", "admin")
    ADMIN_PASS: str = os.getenv("ADMIN_PASS", "admin123")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    DATA_DIR: str = "data"
    CENSOR_WORDS_FILE: str = "censor_words.txt"
    FLUSH_INTERVAL: int = 5
    FLUSH_THRESHOLD: int = 100
    MAX_REVIEW_LENGTH: int = 500
    MIN_REVIEW_LENGTH: int = 1
    MAX_SEMESTERS_PAST: int = 2
