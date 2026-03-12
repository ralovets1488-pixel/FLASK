from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from functools import wraps
from flask import abort
from flask_login import current_user

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице'
login_manager.login_message_category = 'info'


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.role == 'admin':
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.role == 'teacher':
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.role == 'student':
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    import os

    upload_dir = app.config['UPLOAD_FOLDER']

    os.makedirs(upload_dir, exist_ok=True)

    for subdir in ['appointments', 'teachers']:
        subdir_path = os.path.join(upload_dir, subdir)
        os.makedirs(subdir_path, exist_ok=True)

    print(f"✅ Папки для загрузок созданы: {upload_dir}")
    db.init_app(app)
    login_manager.init_app(app)

    from app.routes.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.routes.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.routes.teacher import bp as teacher_bp
    app.register_blueprint(teacher_bp, url_prefix='/teacher')

    from app.routes.student import bp as student_bp
    app.register_blueprint(student_bp, url_prefix='/student')

    return app