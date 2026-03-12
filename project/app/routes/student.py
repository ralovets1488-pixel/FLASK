from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db, student_required
from app.models import User, ConsultationSlot, Appointment, TeacherProfile
from app.forms import AppointmentForm
import os
from werkzeug.utils import secure_filename

bp = Blueprint('student', __name__)


@bp.route('/calendar/<int:teacher_id>')
@bp.route('/calendar/<int:teacher_id>/<string:direction>/<string:current_date>')
@login_required
@student_required
def calendar(teacher_id, direction='current', current_date=None):
    from datetime import datetime, timedelta

    # Получаем преподавателя
    teacher = User.query.get_or_404(teacher_id)
    if teacher.role != 'teacher' or not teacher.is_active:
        flash('Преподаватель не найден', 'danger')
        return redirect(url_for('student.teachers_list'))

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

    # Получаем свободные слоты на неделю
    week_start_dt = datetime.combine(start_of_week, datetime.min.time())
    week_end_dt = datetime.combine(end_of_week, datetime.max.time())

    slots = ConsultationSlot.query.filter(
        ConsultationSlot.teacher_id == teacher_id,
        ConsultationSlot.is_available == True,
        ConsultationSlot.start_time >= week_start_dt,
        ConsultationSlot.start_time <= week_end_dt
    ).order_by(ConsultationSlot.start_time).all()

    # Исключаем слоты, на которые уже записан студент
    booked_slot_ids = [a.slot_id for a in Appointment.query.filter_by(
        student_id=current_user.id,
        status='scheduled'
    ).all()]

    available_slots = [s for s in slots if s.id not in booked_slot_ids]

    slots_by_day = {}
    for day_offset in range(7):
        day = start_of_week + timedelta(days=day_offset)
        slots_by_day[day] = []

    for slot in available_slots:
        slot_date = slot.start_time.date()
        if slot_date in slots_by_day:
            slots_by_day[slot_date].append(slot)

    today_actual = datetime.now().date()

    profile = TeacherProfile.query.filter_by(user_id=teacher_id).first()

    return render_template(
        'student/calendar.html',
        teacher=teacher,
        profile=profile,
        slots_by_day=slots_by_day,
        start_of_week=start_of_week,
        end_of_week=end_of_week,
        today=today_actual,
        current_date=today.strftime('%Y-%m-%d'),
        timedelta=timedelta
    )

@bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    my_appointments = Appointment.query.filter_by(
        student_id=current_user.id
    ).join(ConsultationSlot).order_by(
        ConsultationSlot.start_time.desc()
    ).all()

    return render_template('student/dashboard.html', appointments=my_appointments, current_time=datetime.utcnow())


@bp.route('/teachers')
@login_required
@student_required
def teachers_list():
    teachers = User.query.filter_by(role='teacher', is_active=True).all()
    teacher_profiles = {}
    for t in teachers:
        profile = TeacherProfile.query.filter_by(user_id=t.id).first()
        teacher_profiles[t.id] = profile

    return render_template('student/teachers_list.html', teachers=teachers, teacher_profiles=teacher_profiles)


@bp.route('/teacher/<int:teacher_id>/slots')
@login_required
@student_required
def teacher_slots(teacher_id):
    teacher = User.query.get_or_404(teacher_id)

    if teacher.role != 'teacher' or not teacher.is_active:
        flash('Преподаватель не найден или недоступен', 'danger')
        return redirect(url_for('student.teachers_list'))

    now = datetime.now()
    two_weeks_later = now + timedelta(days=14)

    slots = ConsultationSlot.query.filter(
        ConsultationSlot.teacher_id == teacher_id,
        ConsultationSlot.is_available == True,
        ConsultationSlot.start_time >= now,
        ConsultationSlot.start_time <= two_weeks_later
    ).order_by(ConsultationSlot.start_time).all()

    booked_slot_ids = [a.slot_id for a in Appointment.query.filter_by(
        student_id=current_user.id,
        status='scheduled'
    ).all()]

    available_slots = [s for s in slots if s.id not in booked_slot_ids]
    profile = TeacherProfile.query.filter_by(user_id=teacher_id).first()

    return render_template('student/teacher_slots.html', teacher=teacher, slots=available_slots, profile=profile)


@bp.route('/slot/<int:slot_id>/book', methods=['GET', 'POST'])
@login_required
@student_required
def book_slot(slot_id):
    slot = ConsultationSlot.query.get_or_404(slot_id)
    teacher = User.query.get(slot.teacher_id)

    if not teacher or teacher.role != 'teacher' or not teacher.is_active:
        flash('Преподаватель не найден или недоступен', 'danger')
        return redirect(url_for('student.teachers_list'))

    if not slot.is_available:
        flash('Этот слот уже занят', 'warning')
        return redirect(url_for('student.teacher_slots', teacher_id=slot.teacher_id))

    if slot.start_time < datetime.now():
        flash('Нельзя записаться на прошедшее время', 'danger')
        return redirect(url_for('student.teacher_slots', teacher_id=slot.teacher_id))

    # Проверка конфликта времени (весь час)
    start_hour = slot.start_time.replace(minute=0, second=0, microsecond=0)
    end_hour = start_hour + timedelta(hours=1)

    existing = Appointment.query.join(ConsultationSlot).filter(
        Appointment.student_id == current_user.id,
        Appointment.status == 'scheduled',
        ConsultationSlot.start_time >= start_hour,
        ConsultationSlot.start_time < end_hour
    ).first()

    if existing:
        flash(f'У вас уже есть запись на это время к преподавателю {existing.slot.teacher.username}', 'danger')
        return redirect(url_for('student.teacher_slots', teacher_id=slot.teacher_id))

    form = AppointmentForm()

    # Отладка: показать ошибки валидации
    if request.method == 'POST' and not form.validate():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Ошибка в поле "{field}": {error}', 'danger')
        return render_template('student/book_slot.html', form=form, slot=slot, teacher=teacher)

    if form.validate_on_submit():
        try:
            appointment = Appointment(
                student_id=current_user.id,
                slot_id=slot_id,
                topic=form.topic.data.strip(),
                additional_info=form.additional_info.data.strip() if form.additional_info.data else None,
                status='scheduled'
            )

            # Обработка файла ТОЛЬКО если он загружен и имеет имя
            if form.file.data and form.file.data.filename:
                file = form.file.data
                filename = secure_filename(file.filename)

                # Разрешённые расширения
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'}
                if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
                    flash('Недопустимый тип файла. Разрешены: png, jpg, jpeg, gif, pdf, doc, docx, txt', 'danger')
                    return render_template('student/book_slot.html', form=form, slot=slot, teacher=teacher)

                # Уникальное имя файла
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"student_{current_user.id}_slot_{slot_id}_{timestamp}.{ext}"

                # Путь для сохранения (используем конфигурацию приложения)
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'appointments')
                os.makedirs(upload_path, exist_ok=True)

                # Полный путь к файлу
                file_path = os.path.join(upload_path, unique_filename)
                file.save(file_path)

                # Сохраняем относительный путь для шаблонов
                appointment.file_path = f"uploads/appointments/{unique_filename}"
                flash(f'Файл "{filename}" успешно загружен', 'info')

            # Блокируем слот
            slot.is_available = False

            db.session.add(appointment)
            db.session.commit()

            flash(f'✅ Успешно записаны на консультацию к {teacher.username}!', 'success')
            flash(f'📅 {slot.start_time.strftime("%d.%m.%Y")} в {slot.start_time.strftime("%H:%M")}', 'info')
            return redirect(url_for('student.dashboard'))

        except Exception as e:
            db.session.rollback()
            import traceback
            error_msg = f'Ошибка при записи: {str(e)}'
            print(f"DEBUG ERROR: {error_msg}")
            print(traceback.format_exc())
            flash(error_msg, 'danger')
            return redirect(url_for('student.book_slot', slot_id=slot_id))

    return render_template('student/book_slot.html', form=form, slot=slot, teacher=teacher)


@bp.route('/appointment/<int:appointment_id>/cancel', methods=['POST'])
@login_required
@student_required
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)

    if appointment.student_id != current_user.id:
        flash('Нет доступа к этой записи', 'danger')
        return redirect(url_for('student.dashboard'))

    if appointment.slot.start_time < datetime.now():
        flash('Нельзя отменить прошедшую консультацию', 'danger')
        return redirect(url_for('student.dashboard'))

    # Возвращаем слот в доступные
    appointment.slot.is_available = True
    appointment.status = 'cancelled'

    db.session.commit()
    flash('Запись успешно отменена', 'success')
    return redirect(url_for('student.dashboard'))