import os
import uuid
import json
import hashlib
import mimetypes
from datetime import datetime
from flask import Flask, request, render_template, redirect, flash, url_for, send_from_directory

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'uploads'
DATA_FILE = 'data.json'
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.txt', '.pdf', '.docx'}
DISALLOWED_EXTENSIONS = {'.exe', '.sh', '.php', '.js'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

try:
    if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
    else:
        file_data = []
except (json.JSONDecodeError, IOError):
    file_data = []
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(file_data, f, indent=2)

def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def save_metadata():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(file_data, f, indent=2)

def is_allowed(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS and ext not in DISALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Файл не выбран')
            return redirect(request.url)

        uploaded_file = request.files['file']
        if uploaded_file.filename == '':
            flash('Имя файла пустое')
            return redirect(request.url)

        if not is_allowed(uploaded_file.filename):
            flash('Недопустимый тип файла')
            return redirect(request.url)

        temp_path = os.path.join(UPLOAD_FOLDER, 'temp')
        uploaded_file.save(temp_path)
        file_md5 = calculate_md5(temp_path)

        for entry in file_data:
            if entry['md5'] == file_md5:
                flash('Файл с таким содержимым уже загружен')
                os.remove(temp_path)
                return redirect(request.url)

        file_uuid = uuid.uuid4().hex
        ext = os.path.splitext(uploaded_file.filename)[1].lower()
        subdir = os.path.join(file_uuid[:2], file_uuid[2:4])
        full_path = os.path.join(UPLOAD_FOLDER, subdir)
        os.makedirs(full_path, exist_ok=True)
        final_filename = f"{file_uuid}{ext}"
        final_path = os.path.join(full_path, final_filename)
        os.rename(temp_path, final_path)

        file_entry = {
            "uuid": file_uuid,
            "original_name": uploaded_file.filename,
            "upload_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "path": os.path.join('uploads', subdir, final_filename).replace('\\', '/'),
            "extension": ext,
            "md5": file_md5
        }
        file_data.append(file_entry)
        save_metadata()

        flash('Файл успешно загружен')
        return redirect(url_for('index'))

    return render_template('index.html', files=file_data[::-1])

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
