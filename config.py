"""Configuración central de New Records."""

import os
from datetime import timedelta
from urllib.parse import quote_plus

from dotenv import load_dotenv


load_dotenv()


class Config:
    """Valores compartidos por la aplicación Flask."""

    DB_USER = os.getenv("DB_USER", "new_records_app")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "new_records_db")

    SQLALCHEMY_DATABASE_URI = (
        "postgresql+psycopg2://"
        f"{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

    # Sesiones y formularios
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    WTF_CSRF_TIME_LIMIT = 3600

    # Roles técnicos de PostgreSQL y herramientas de respaldo/restauración
    DB_ADMIN_USER = os.getenv("DB_ADMIN_USER", "new_records_admin")
    DB_ADMIN_PASSWORD = os.getenv("DB_ADMIN_PASSWORD", "")
    DB_BACKUP_USER = os.getenv("DB_BACKUP_USER", "new_records_backup")
    DB_BACKUP_PASSWORD = os.getenv("DB_BACKUP_PASSWORD", "")
    POSTGRES_BIN = os.getenv("POSTGRES_BIN", "")

    # Correo electrónico (PIN y notificaciones)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "1") == "1"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "ventas@newrecords.local")

