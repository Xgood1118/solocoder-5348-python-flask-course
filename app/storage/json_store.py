import json
import os
import threading
import time
from typing import Self, Type, TypeVar, Generic, Optional
from dataclasses import dataclass

from app.config import Config
from app.models.dataclasses import (
    Course,
    Enrollment,
    Teacher,
    Student,
    Review,
    Semester,
)

T = TypeVar("T", Course, Enrollment, Teacher, Student, Review, Semester)


class JsonStore(Generic[T]):
    _instances: dict[str, "JsonStore"] = {}
    _lock: threading.Lock = threading.Lock()
    _write_count: int = 0
    _last_flush: float = time.time()
    _flush_thread: Optional[threading.Thread] = None
    _flush_stop_event: threading.Event = threading.Event()

    def __new__(cls, table_name: str, model_class: Type[T]) -> Self:
        with cls._lock:
            if table_name not in cls._instances:
                instance = super().__new__(cls)
                instance._init(table_name, model_class)
                cls._instances[table_name] = instance
            return cls._instances[table_name]

    def _init(self, table_name: str, model_class: Type[T]) -> None:
        self.table_name = table_name
        self.model_class = model_class
        self._data_lock = threading.Lock()
        self._data: dict[str, T] = {}
        self._dirty: bool = False
        self._load_from_disk()

    @classmethod
    def _ensure_data_dir(cls) -> None:
        if not os.path.exists(Config.DATA_DIR):
            os.makedirs(Config.DATA_DIR)

    def _get_file_path(self) -> str:
        return os.path.join(Config.DATA_DIR, f"{self.table_name}.json")

    def _load_from_disk(self) -> None:
        self._ensure_data_dir()
        file_path = self._get_file_path()
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return

        with open(file_path, "r", encoding="utf-8") as f:
            try:
                raw_data = json.load(f)
                with self._data_lock:
                    self._data = {}
                    for item in raw_data:
                        obj = self.model_class.from_dict(item)
                        self._data[obj.id] = obj
            except json.JSONDecodeError:
                with self._data_lock:
                    self._data = {}

    def _flush_to_disk(self) -> None:
        if not self._dirty:
            return

        file_path = self._get_file_path()
        with self._data_lock:
            data_list = [obj.to_dict() for obj in self._data.values()]
            self._dirty = False

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data_list, f, ensure_ascii=False, indent=2)

    @classmethod
    def start_flush_thread(cls) -> None:
        if cls._flush_thread is not None and cls._flush_thread.is_alive():
            return

        cls._flush_stop_event.clear()
        cls._flush_thread = threading.Thread(target=cls._flush_worker, daemon=True)
        cls._flush_thread.start()

    @classmethod
    def stop_flush_thread(cls) -> None:
        cls._flush_stop_event.set()
        if cls._flush_thread:
            cls._flush_thread.join(timeout=Config.FLUSH_INTERVAL + 1)
        cls.flush_all()

    @classmethod
    def _flush_worker(cls) -> None:
        while not cls._flush_stop_event.is_set():
            time.sleep(Config.FLUSH_INTERVAL)
            need_flush = False
            with cls._lock:
                if time.time() - cls._last_flush >= Config.FLUSH_INTERVAL:
                    need_flush = True
            if need_flush:
                cls.flush_all()

    @classmethod
    def flush_all(cls) -> None:
        with cls._lock:
            instances = list(cls._instances.values())
            cls._last_flush = time.time()
            cls._write_count = 0
        for instance in instances:
            instance._flush_to_disk()

    def _mark_dirty(self) -> None:
        need_flush = False
        with self.__class__._lock:
            self.__class__._write_count += 1
            if self.__class__._write_count >= Config.FLUSH_THRESHOLD:
                need_flush = True
        if need_flush:
            self.__class__.flush_all()

    def get_all(self) -> list[T]:
        with self._data_lock:
            return list(self._data.values())

    def get_by_id(self, obj_id: str) -> Optional[T]:
        with self._data_lock:
            return self._data.get(obj_id)

    def add(self, obj: T) -> None:
        with self._data_lock:
            self._data[obj.id] = obj
            self._dirty = True
        self._mark_dirty()

    def update(self, obj: T) -> None:
        with self._data_lock:
            if obj.id in self._data:
                self._data[obj.id] = obj
                self._dirty = True
        self._mark_dirty()

    def delete(self, obj_id: str) -> bool:
        deleted = False
        with self._data_lock:
            if obj_id in self._data:
                del self._data[obj_id]
                self._dirty = True
                deleted = True
        if deleted:
            self._mark_dirty()
            return True
        return False

    def exists(self, obj_id: str) -> bool:
        with self._data_lock:
            return obj_id in self._data

    def filter(self, **kwargs) -> list[T]:
        results = []
        with self._data_lock:
            for obj in self._data.values():
                match = True
                for key, value in kwargs.items():
                    if not hasattr(obj, key) or getattr(obj, key) != value:
                        match = False
                        break
                if match:
                    results.append(obj)
        return results

    def count(self) -> int:
        with self._data_lock:
            return len(self._data)


course_store: JsonStore[Course] = JsonStore("courses", Course)
enrollment_store: JsonStore[Enrollment] = JsonStore("enrollments", Enrollment)
teacher_store: JsonStore[Teacher] = JsonStore("teachers", Teacher)
student_store: JsonStore[Student] = JsonStore("students", Student)
review_store: JsonStore[Review] = JsonStore("reviews", Review)
semester_store: JsonStore[Semester] = JsonStore("semesters", Semester)
