from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FileField, DateTimeLocalField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User


class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Имя пользователя уже занято.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email уже зарегистрирован.')


class ConsultationSlotForm(FlaskForm):
    start_time = DateTimeLocalField('Дата и время начала', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    submit = SubmitField('Создать слот')


class AppointmentForm(FlaskForm):
    topic = StringField('Тема консультации', validators=[DataRequired(), Length(max=200)])
    additional_info = TextAreaField('Дополнительная информация')
    file = FileField('Файл (необязательно)')
    submit = SubmitField('Записаться')


class TeacherProfileForm(FlaskForm):
    bio = TextAreaField('О себе', validators=[Length(max=1000, message="Не более 1000 символов")])
    specialization = StringField('Специализация', validators=[Length(max=200, message="Не более 200 символов")])
    photo = FileField('Фотография', description='Поддерживаются форматы: JPG, PNG, GIF')
    submit = SubmitField('Сохранить')


class UserManagementForm(FlaskForm):
    role = SelectField('Роль',
                       choices=[('student', 'Студент'), ('teacher', 'Преподаватель'), ('admin', 'Администратор')])
    is_active = SelectField('Статус', choices=[('1', 'Активен'), ('0', 'Заблокирован')])
    submit = SubmitField('Сохранить')