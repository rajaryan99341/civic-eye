import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
class Config:
    SECRET_KEY = os.environ.get("CIVIC_EYE_SECRET", "civic-eye-dev-secret-change-me")
    DATABASE_PATH = os.environ.get("CIVIC_EYE_DB", os.path.join(BASE_DIR, "civic_eye.db"))
    UPLOAD_FOLDER = os.environ.get("CIVIC_EYE_UPLOADS", os.path.join(BASE_DIR, "uploads"))
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    TOKEN_HOURS = 24
    DUPLICATE_RADIUS_METERS = 80
    DUPLICATE_HASH_THRESHOLD = 12
    CORS_ORIGINS = os.environ.get("CIVIC_EYE_CORS", "http://localhost:5173").split(",")
