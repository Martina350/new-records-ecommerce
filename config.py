"""Configuración central de New Records."""

import os
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
    SECRET_KEY = os.getenv("SECRET_KEY", "clave-temporal-solo-desarrollo")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

    # Correo electrónico (PIN y notificaciones)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "1") == "1"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "ventas@newrecords.local")

