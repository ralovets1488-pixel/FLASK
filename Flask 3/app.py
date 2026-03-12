from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
import json, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'

JSON_PATH = 'users.json'

def load_users():
    if not os.path.exists(JSON_PATH):
        with open(JSON_PATH, 'w') as f:
            json.dump({}, f)
    with open(JSON_PATH, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(JSON_PATH, 'w') as f:
        json.dump(users, f, indent=4)

class LoginForm(FlaskForm):
    username = StringField("Имя пользователя", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Войти")

class RegisterForm(FlaskForm):
    username = StringField("Имя пользователя", validators=[DataRequired(), Length(min=3)])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(min=8)])
    confirm = PasswordField("Повторите пароль", validators=[EqualTo('password', message='Пароли не совпадают')])
    submit = SubmitField("Создать пользователя")

def bad_password(pw):
    return len(pw) < 8 or pw.isdigit() or pw.isalpha()

@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        users = load_users()
        user = users.get(form.username.data)
        if user and check_password_hash(user['password'], form.password.data):
            session['user'] = form.username.data
            user['last_login'] = datetime.now().isoformat()
            save_users(users)
            return redirect(url_for('register'))
        flash("Неверный логин или пароль")
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' not in session:
        return redirect(url_for('login'))

    form = RegisterForm()
    if form.validate_on_submit():
        users = load_users()
        username = form.username.data

        if username in users:
            flash("Пользователь уже существует")
        elif bad_password(form.password.data):
            flash("Слишком простой пароль")
        else:
            users[username] = {
                'password': generate_password_hash(form.password.data),
                'registered': datetime.now().isoformat(),
                'last_login': None
            }
            save_users(users)
            flash(f"Пользователь {username} создан")
            return redirect(url_for('register'))

    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
