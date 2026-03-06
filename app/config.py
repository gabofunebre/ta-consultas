import os


def _env_or_none(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _build_database_url() -> str:
    user = _env_or_none('DB_USER') or _env_or_none('POSTGRES_USER') or 'postgres'
    password = _env_or_none('DB_PASSWORD') or _env_or_none('POSTGRES_PASSWORD') or 'postgres'
    host = _env_or_none('DB_HOST') or _env_or_none('POSTGRES_HOST') or 'localhost'
    port = _env_or_none('DB_PORT') or _env_or_none('POSTGRES_PORT') or '5432'
    db_name = _env_or_none('DB_NAME') or _env_or_none('POSTGRES_DB') or 'consultas_db'
    return f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}'


class Config:
    SECRET_KEY = _env_or_none('SECRET_KEY') or 'cambiar-esta-clave'
    SQLALCHEMY_DATABASE_URI = _env_or_none('DATABASE_URL') or _build_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = _env_or_none('UPLOAD_FOLDER') or '/app/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
