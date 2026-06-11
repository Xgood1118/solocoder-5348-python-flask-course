import os
import signal
import sys
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

load_dotenv()

from app.config import Config
from app.utils.response import success_response, register_error_handlers
from app.storage.json_store import JsonStore
from app.routes.students import students_bp
from app.routes.teachers import teachers_bp
from app.routes.courses import courses_bp
from app.routes.reviews import reviews_bp
from app.routes.admin import admin_bp
from app.routes.base import base_bp


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    register_error_handlers(app)

    @app.route("/healthz", methods=["GET"])
    def healthz():
        return success_response({"status": "ok"})

    app.register_blueprint(students_bp, url_prefix="/students")
    app.register_blueprint(teachers_bp, url_prefix="/teachers")
    app.register_blueprint(courses_bp, url_prefix="/courses")
    app.register_blueprint(reviews_bp, url_prefix="/reviews")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(base_bp, url_prefix="")

    JsonStore.start_flush_thread()

    def shutdown_handler(signum, frame):
        print("\n正在优雅关闭服务，保存数据...")
        JsonStore.stop_flush_thread()
        JsonStore.flush_all()
        print("数据保存完成，服务已关闭。")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    return app


if __name__ == "__main__":
    app = create_app()
    try:
        app.run(host="0.0.0.0", port=Config.PORT, debug=False, use_reloader=False)
    finally:
        JsonStore.flush_all()
