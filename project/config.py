import os
from datetime import timedelta


class Config:
    # fixme
    SECRET_KEY = '12345678'
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'consultations.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Настройки загрузки файлов
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    PERMANENT_SESSION_LIFETIME = timedelta(days=7)