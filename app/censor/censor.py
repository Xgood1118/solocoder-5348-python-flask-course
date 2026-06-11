import os
import threading
from dataclasses import dataclass
from typing import Self

from app.config import Config


@dataclass
class CensorResult:
    text: str
    has_sensitive: bool
    hit_words: list[str]


class WordCensor:
    _instance: Self | None = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> Self:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init()
            return cls._instance

    def _init(self) -> None:
        self._words_lock = threading.Lock()
        self._words: list[str] = []
        self._load_words()

    def _load_words(self) -> None:
        words: list[str] = []
        if os.path.exists(Config.CENSOR_WORDS_FILE):
            with open(Config.CENSOR_WORDS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip()
                    if word and not word.startswith("#"):
                        words.append(word)
        with self._words_lock:
            self._words = words

    def reload_words(self, words: list[str] | None = None) -> None:
        if words is not None:
            cleaned_words = [w.strip() for w in words if w.strip()]
            with open(Config.CENSOR_WORDS_FILE, "w", encoding="utf-8") as f:
                for word in cleaned_words:
                    f.write(f"{word}\n")
            with self._words_lock:
                self._words = cleaned_words
        else:
            self._load_words()

    def censor(self, text: str) -> CensorResult:
        hit_words: list[str] = []
        censored_text = text

        with self._words_lock:
            words = list(self._words)

        for word in words:
            if word in censored_text:
                hit_words.append(word)
                censored_text = censored_text.replace(word, "***")

        return CensorResult(
            text=censored_text,
            has_sensitive=len(hit_words) > 0,
            hit_words=hit_words,
        )

    def get_words(self) -> list[str]:
        with self._words_lock:
            return list(self._words)


word_censor: WordCensor = WordCensor()
