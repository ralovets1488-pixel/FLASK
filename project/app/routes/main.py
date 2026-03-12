from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user
from app.models import User, TeacherProfile

bp = Blueprint('main', __name__)

@bp.route('/')
@bp.route('/index')
def index():
    # ВСЕГДА показываем главную страницу, независимо от авторизации
    teachers = User.query.filter_by(role='teacher', is_active=True).all()
    teacher_profiles = {t.id: TeacherProfile.query.filter_by(user_id=t.id).first() for t in teachers}
    return render_template('index.html', teachers=teachers, teacher_profiles=teacher_profiles)