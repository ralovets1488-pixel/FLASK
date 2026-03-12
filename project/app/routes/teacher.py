from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from app import db, teacher_required
from app.models import ConsultationSlot, Appointment, User
from app.forms import ConsultationSlotForm, TeacherProfileForm
import os

bp = Blueprint('teacher', __name__)


@bp.route('/calendar')
@bp.route('/calendar/<string:direction>/<string:current_date>')
@login_required
@teacher_required
def calendar(direction='current', current_date=None):
    from datetime import datetime, timedelta

    # Определяем текущую дату для календаря
    if current_date:
        try:
            today = datetime.strptime(current_date, '%Y-%m-%d').date()
        except:
            today = datetime.now().date()
    else:
        today = datetime.now().date()

    # Навигация по неделям
    if direction == 'next':
        today = today + timedelta(days=7)
    elif direction == 'prev':
        today = today - timedelta(days=7)

    # Понедельник текущей недели
    start_of_week = today - timedelta(days=today.weekday())
    # Воскресенье текущей недели
    end_of_week = start_of_week + timedelta(days=6)

    # Получаем все слоты на неделю
    week_start_dt = datetime.combine(start_of_week, datetime.min.time())
    week_end_dt = datetime.combine(end_of_week, datetime.max.time())

    slots = ConsultationSlot.query.filter(
        ConsultationSlot.teacher_id == current_user.id,
        ConsultationSlot.start_time >= week_start_dt,
        ConsultationSlot.start_time <= week_end_dt
    ).order_by(ConsultationSlot.start_time).all()

    # Группируем слоты по дням
    slots_by_day = {}
    for day_offset in range(7):
        day = start_of_week + timedelta(days=day_offset)
        slots_by_day[day] = []

    for slot in slots:
        slot_date = slot.start_time.date()
        if slot_date in slots_by_day:
            slots_by_day[slot_date].append(slot)

    # Определяем сегодняшнюю дату для выделения
    today_actual = datetime.now().date()

    return render_template(
        'teacher/calendar.html',
        slots_by_day=slots_by_day,
        start_of_week=start_of_week,
        end_of_week=end_of_week,
        today=today_actual,
        current_date=today.strftime('%Y-%m-%d'),
        timedelta=timedelta
    )

@bp.route('/dashboard')
@login_required
@teacher_required
def dashboard():
    from datetime import datetime, timedelta

    # Слоты на текущую неделю (понедельник-воскресенье)
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())  # Понедельник
    end_of_week = start_of_week + timedelta(days=7)  # Следующий понедельник

    slots = ConsultationSlot.query.filter(
        ConsultationSlot.teacher_id == current_user.id,
        ConsultationSlot.start_time >= datetime.combine(start_of_week, datetime.min.time()),
        ConsultationSlot.start_time < datetime.combine(end_of_week, datetime.min.time())
    ).order_by(ConsultationSlot.start_time).all()

    # Форма для быстрого создания слота
    form = ConsultationSlotForm()

    return render_template('teacher/dashboard.html', slots=slots, form=form)


@bp.route('/slot/create', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_slot():
    form = ConsultationSlotForm()
    if form.validate_on_submit():
        start_time = form.start_time.data

        # Проверка: время должно начинаться с 00 минут
        if start_time.minute != 0:
            flash('Время должно начинаться с 00 минут (например, 14:00)', 'danger')
            return redirect(url_for('teacher.create_slot'))

        # Проверка: не пересекается ли со существующим слотом
        existing = ConsultationSlot.query.filter_by(
            teacher_id=current_user.id,
            start_time=start_time
        ).first()

        if existing:
            flash('Слот на это время уже существует', 'danger')
            return redirect(url_for('teacher.create_slot'))

        slot = ConsultationSlot(teacher_id=current_user.id, start_time=start_time)
        db.session.add(slot)
        db.session.commit()
        flash('Слот успешно создан', 'success')
        return redirect(url_for('teacher.dashboard'))

    return render_template('teacher/create_slot.html', form=form)


@bp.route('/slot/<int:slot_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_slot(slot_id):
    slot = ConsultationSlot.query.get_or_404(slot_id)

    if slot.teacher_id != current_user.id:
        flash('Нет доступа к этому слоту', 'danger')
        return redirect(url_for('teacher.dashboard'))

    # Проверка: есть ли активные записи
    active_appointments = Appointment.query.filter_by(
        slot_id=slot_id,
        status='scheduled'
    ).count()

    if active_appointments > 0:
        flash('Нельзя удалить слот с активными записями', 'warning')
        return redirect(url_for('teacher.dashboard'))

    db.session.delete(slot)
    db.session.commit()
    flash('Слот успешно удален', 'success')
    return redirect(url_for('teacher.dashboard'))


@bp.route('/appointment/<int:appointment_id>/mark_attended/<int:attended>')
@login_required
@teacher_required
def mark_attended(appointment_id, attended):
    appointment = Appointment.query.get_or_404(appointment_id)
    slot = appointment.slot

    if slot.teacher_id != current_user.id:
        flash('Нет доступа к этой записи', 'danger')
        return redirect(url_for('teacher.dashboard'))

    appointment.attended = bool(attended)
    appointment.status = 'completed'
    db.session.commit()
    flash('Статус посещения обновлен', 'success')
    return redirect(url_for('teacher.dashboard'))


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
@teacher_required
def profile():
    from datetime import datetime
    import os
    from werkzeug.utils import secure_filename

    form = TeacherProfileForm()

    # Заполняем форму текущими данными при загрузке страницы
    if request.method == 'GET' and current_user.teacher_profile:
        form.bio.data = current_user.teacher_profile.bio
        form.specialization.data = current_user.teacher_profile.specialization

    if form.validate_on_submit():
        # Создаём профиль, если его нет
        if not current_user.teacher_profile:
            profile = TeacherProfile(user_id=current_user.id)
            db.session.add(profile)
            db.session.flush()  # Получаем ID для сохранения файла
        else:
            profile = current_user.teacher_profile

        # Сохраняем текстовые поля
        profile.bio = form.bio.data.strip() if form.bio.data else None
        profile.specialization = form.specialization.data.strip() if form.specialization.data else None
        profile.is_available = True  # Преподаватель активен

        # Обработка фото ТОЛЬКО если файл загружен
        if form.photo.data and form.photo.data.filename:
            try:
                file = form.photo.data
                filename = secure_filename(file.filename)

                # Проверяем расширение
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
                    flash('Недопустимый формат файла. Разрешены: png, jpg, jpeg, gif', 'danger')
                    return redirect(url_for('teacher.profile'))

                # Уникальное имя файла
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"teacher_{current_user.id}_{timestamp}.{ext}"

                # Путь сохранения
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'teachers')
                os.makedirs(upload_path, exist_ok=True)

                # Сохраняем файл
                file_path = os.path.join(upload_path, unique_filename)
                file.save(file_path)

                # Сохраняем путь в БД
                profile.photo_path = f"uploads/teachers/{unique_filename}"
                flash('Фотография успешно загружена', 'success')

            except Exception as e:
                flash(f'Ошибка загрузки файла: {str(e)}', 'danger')

        db.session.commit()
        flash('Профиль успешно обновлён!', 'success')
        return redirect(url_for('teacher.profile'))

    return render_template('teacher/profile.html', form=form)