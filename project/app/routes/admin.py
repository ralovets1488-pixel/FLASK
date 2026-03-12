from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db, admin_required
from app.models import User, TeacherProfile
from app.forms import UserManagementForm

bp = Blueprint('admin', __name__)


@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    users = User.query.all()
    return render_template('admin/dashboard.html', users=users)


@bp.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserManagementForm()

    if form.validate_on_submit():
        user.role = form.role.data
        user.is_active = form.is_active.data == '1'

        # Если назначаем преподавателем и нет профиля - создаем
        if user.role == 'teacher' and not user.teacher_profile:
            profile = TeacherProfile(user_id=user.id)
            db.session.add(profile)

        db.session.commit()
        flash('Пользователь успешно обновлен', 'success')
        return redirect(url_for('admin.dashboard'))

    form.role.data = user.role
    form.is_active.data = '1' if user.is_active else '0'
    return render_template('admin/edit_user.html', form=form, user=user)