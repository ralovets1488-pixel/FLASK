"""
Инициализация базы данных и создание тестовых пользователей
"""
from app import create_app, db
from app.models import User, TeacherProfile
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Создаём все таблицы
    db.create_all()
    print("✅ Таблицы базы данных созданы")

    # Проверяем, есть ли уже администратор
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@consult.edu',
            role='admin',
            is_active=True
        )
        admin.password_hash = generate_password_hash('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Администратор создан:")
        print("   Логин: admin")
        print("   Пароль: admin123")
    else:
        print("ℹ️ Администратор уже существует")

    # Создаём тестовых преподавателей
    teachers_data = [
        {'username': 'ivanov', 'email': 'ivanov@edu.ru', 'specialization': 'Высшая математика'},
        {'username': 'petrov', 'email': 'petrov@edu.ru', 'specialization': 'Программирование'},
        {'username': 'sidorova', 'email': 'sidorova@edu.ru', 'specialization': 'Физика'},
    ]

    for teacher_data in teachers_data:
        teacher = User.query.filter_by(username=teacher_data['username']).first()
        if not teacher:
            teacher = User(
                username=teacher_data['username'],
                email=teacher_data['email'],
                role='teacher',
                is_active=True
            )
            teacher.password_hash = generate_password_hash('teacher123')
            db.session.add(teacher)
            db.session.flush()  # Получаем ID для профиля

            # Создаём профиль преподавателя
            profile = TeacherProfile(
                user_id=teacher.id,
                specialization=teacher_data['specialization'],
                bio=f"Преподаватель по специализации: {teacher_data['specialization']}",
                is_available=True
            )
            db.session.add(profile)
            print(f"✅ Преподаватель {teacher_data['username']} создан")

    db.session.commit()
    print("\n✅ База данных успешно инициализирована!")
    print("\nДанные для входа:")
    print("- Администратор: admin / admin123")
    print("- Преподаватели: ivanov, petrov, sidorova / teacher123")