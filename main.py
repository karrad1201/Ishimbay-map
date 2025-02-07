import os
import json
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename

static_folder = os.path.abspath("static")
UPLOAD_FOLDER = os.path.join(static_folder, 'uploads')
app = Flask(__name__, template_folder="templates", static_folder=static_folder)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "super secret key" #  Обязательно нужен для flash

# Создаем папку uploads, если ее нет
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
def load_data():
    with open(os.path.join("static", "streets_data.json"), 'r', encoding='utf-8') as f:
        streets = json.load(f)
    return streets

def save_data(streets):
    with open("streets_data.json", 'w', encoding='utf-8') as f:
        json.dump(streets, f, ensure_ascii=False, indent=4)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/admin/add_page', methods=['POST'])
def admin_add_page():
    streets_data = load_data()
    street_id = request.form['street_id']
    street = next((s for s in streets_data if s['id'] == street_id), None)
    if street is None:
        return "Street not found", 404

    # Создаем новую пустую страницу
    new_page = {
        'title': '',
        'content': '',
        'photo': ''
    }

    # Добавляем новую страницу в список страниц
    street['pages'].append(new_page)

    # Сохраняем изменения в streets_data.json
    save_data(streets_data)

    # Перенаправляем пользователя обратно на страницу редактирования
    return redirect(url_for('admin_edit_form', street_id=street_id))
# Функция для отображения формы редактирования
@app.route('/admin/edit', methods=['GET'])
def admin_edit_form():
    street_id = request.args.get('street_id')
    if street_id is None or not street_id.isdigit():
        return "Invalid street ID", 400

    street_id = int(street_id)
    streets_data = load_data()
    street = next((s for s in streets_data if int(s['id']) == street_id), None)

    if street is None:
        return "Street not found", 404

    return render_template('admin_edit.html', street=street, streets_data=streets_data)


# Функция для сохранения данных
@app.route('/admin/edit', methods=['POST'])
def admin_edit_save():
    streets_data = load_data()
    street_id = request.form['street_id']  # Получаем street_id из формы
    street = next((s for s in streets_data if s['id'] == street_id), None)
    if street is None:
        return "Street not found", 404

    page_index_to_update = int(request.form['page_index']) - 1

    # Обработка удаления фото
    if 'delete_photo' in request.form:
        page = street['pages'][page_index_to_update]
        photo_path = page['photo']
        if photo_path:
            full_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_path)  # Правильный путь к файлу
            try:
                os.remove(full_photo_path)
                print(f"Удален файл: {full_photo_path}")
                flash(f"Удален файл: {photo_path}")
            except FileNotFoundError:
                print(f"Файл не найден: {full_photo_path}")
                flash(f"Файл не найден: {photo_path}")
            page['photo'] = ""

    # Обработка загрузки файла
    file_field_name = f'page-{page_index_to_update+1}-photo'
    if file_field_name in request.files:
        file = request.files[file_field_name]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                file.save(filepath)
                street['pages'][page_index_to_update]['photo'] = filename  # Сохраняем только имя файла!!!
                print(f"Сохраняем имя файла: {filename}")  # <-- Добавили print
                flash(f"Сохранен файл: {filename}")
            except Exception as e:
                print(f"Ошибка при сохранении файла: {e}")
                flash(f"Ошибка при сохранении файла: {e}")  # Показываем сообщение об ошибке

    # Обновляем остальные атрибуты страницы
    street['pages'][page_index_to_update]['title'] = request.form.get(f'page-{page_index_to_update+1}-title', '')
    street['pages'][page_index_to_update]['content'] = request.form.get(f'page-{page_index_to_update+1}-content', '')

    # Обновляем остальные атрибуты улицы только на первой странице
    if page_index_to_update == 0:
        street['name'] = request.form['name']
        street['city'] = request.form['city']
        street['class'] = request.form['class']
        street['lat'] = request.form['lat']
        street['lon'] = request.form['lon']
        street['nominatimQuery'] = request.form['nominatimQuery']
        street['panorama'] = request.form['panorama']
        street['type'] = request.form['type']

    # Важно: Сохраняем данные после изменений
    save_data(streets_data)
    return redirect(url_for('admin_edit_form', street_id=street_id))  # Редирект на GET-запрос


@app.route('/uploads/<filename>')
def serve_portrets(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/adm')
def admin():
    streets_data = load_data()
    return render_template('adm.html', streets_data=streets_data)

@app.route('/')
def index():
    streets_data = load_data()
    return render_template('index.html', streets_data=streets_data)

if __name__ == '__main__':
    app.run(debug=True)
