import os


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'cambiar-esta-clave')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql+psycopg2://postgres:postgres@db:5432/consultas_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/app/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
