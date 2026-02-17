import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "dev-secret-key-change-in-production"
    )

    # Supabase PostgreSQL (Session Pooler — IPv4 compatible)
    DATABASE_URL = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres.qtkrrwtorkmfhxakemjp:Anees%40983795@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"
    )

    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
    }

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "reports")

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
