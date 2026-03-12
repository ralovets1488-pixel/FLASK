from datetime import datetime
from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='student')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher_profile = db.relationship('TeacherProfile', backref='user', uselist=False)
    appointments_as_student = db.relationship('Appointment', foreign_keys='Appointment.student_id', backref='student',
                                              lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class TeacherProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bio = db.Column(db.Text)
    specialization = db.Column(db.String(200))
    photo_path = db.Column(db.String(200))
    is_available = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<TeacherProfile {self.user.username}>'


class ConsultationSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='slots')
    appointments = db.relationship('Appointment', backref='slot', lazy='select')

    def __repr__(self):
        return f'<ConsultationSlot {self.start_time}>'


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('consultation_slot.id'), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    additional_info = db.Column(db.Text)
    file_path = db.Column(db.String(200))
    status = db.Column(db.String(20), default='scheduled')
    attended = db.Column(db.Boolean, default=None)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('student_id', 'slot_id', name='_student_slot_uc'),)

    def __repr__(self):
        return f'<Appointment {self.topic}>'