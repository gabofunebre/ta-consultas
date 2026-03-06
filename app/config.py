import os


def _build_database_url() -> str:
    user = os.getenv('DB_USER') or os.getenv('POSTGRES_USER', 'postgres')
    password = os.getenv('DB_PASSWORD') or os.getenv('POSTGRES_PASSWORD', 'postgres')
    host = os.getenv('DB_HOST') or os.getenv('POSTGRES_HOST') or 'localhost'
    port = os.getenv('DB_PORT') or os.getenv('POSTGRES_PORT', '5432')
    db_name = os.getenv('DB_NAME') or os.getenv('POSTGRES_DB', 'consultas_db')
    return f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}'


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'cambiar-esta-clave')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', _build_database_url())
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/app/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
