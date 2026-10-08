import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "instance", "internship.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "resumes")
    ALLOWED_RESUME_EXTENSIONS = {"pdf"}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max upload

    # Seed / default admin credentials (used only by init_db.py, can be overridden via env vars)
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@college.edu")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@123")
