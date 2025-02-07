import os
from flask import Flask, render_template

static_folder = os.path.abspath("static")  # Определяем static_folder здесь

app = Flask(__name__, template_folder="templates", static_folder=static_folder)  # Передаем static_folder в Flask

# Получаем абсолютный путь к папке templates
template_path = os.path.abspath("templates")
print(f"Absolute path to templates folder: {template_path}")

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # разрешенные расширения

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
def load_data():
    import json  # Импортируем json здесь
    DATA_FILE = os.path.join(static_folder, 'streets_data.json')
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    DATA_FILE = os.path.join(static_folder, 'streets_data.json')  # Используем static_folder здесь
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False, sort_keys=True)

def get_next_id(data):
    max_id = 0
    for item in data:
        if 'id' in item and isinstance(item['id'], (int, str)):
            try:
                current_id = int(item['id'])
                max_id = max(max_id, current_id)
            except ValueError:
                pass
    return str(max_id + 1)

@app.route('/')
def index():
    streets_data = load_data()
    for street in streets_data:
        street['static_url'] = '/static'
    return render_template('index.html', streets_data=streets_data)

@app.route('/adm')
def admin():
    streets_data = load_data()
    return render_template('adm.html', streets_data=streets_data)

@app.route('/admin/edit', methods=['GET', 'POST'])
def admin_edit():
    streets_data = load_data()
    if request.method == 'GET':
        street_id = request.args.get('street_id')
        if street_id is None or not street_id.isdigit():
            return "Invalid street ID", 400

        street_id = int(street_id)
        street = next((s for s in streets_data if int(s['id']) == street_id), None)

        if street is None:
            return "Street not found", 404

        return render_template('admin_edit.html', street=street, streets_data=streets_data)

    elif request.method == 'POST':
        street_id = request.form['street_id']
        street = next((s for s in streets_data if s['id'] == street_id), None)
        if street is None:
            return "Street not found", 404

        page_index_to_update = int(request.form['page_index']) - 1

        # Обработка удаления фото
        if 'delete_photo' in request.form:
            page = street['pages'][page_index_to_update]
            photo_path = page['photo']
            if photo_path:
                full_photo_path = os.path.join(app.static_folder, photo_path)
                try:
                    os.remove(full_photo_path)  # удаляем файл с сервера
                    print(f"Удален файл: {full_photo_path}")
                except FileNotFoundError:
                    print(f"Файл не найден: {full_photo_path}")
                page['photo'] = ""  # очищаем поле photo в JSON

        # Обработка загрузки файла
        file_field_name = f'page-{page_index_to_update+1}-photo'
        if file_field_name in request.files:
            file = request.files[file_field_name]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                street['pages'][page_index_to_update]['photo'] = 'portrets/' + filename  # Сохраняем путь к файлу
                print(f"Сохраняем путь к файлу: portrets/{filename}")  # <-- Добавили print

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

        # Важно:  Сохраняем данные после изменений
        save_data(streets_data)
        return redirect(url_for('admin_edit', street_id=street_id))

@app.route('/admin/add', methods=['POST'])
def admin_add():
    streets_data = load_data()
    new_id = get_next_id(streets_data)
    new_street = {
        "city": "",
        "class": "",
        "id": str(new_id),
        "lat": "",
        "lon": "",
        "name": "Новая улица",
        "nominatimQuery": "",
        "panorama": "",
        "type": "",
        "photo": "",  # <--- Добавлено поле photo с пустой строкой
        "pages": [
            {
                "title": "",
                "content": "",
                "photo": ""
            }
        ]
    }
    streets_data.append(new_street)
    save_data(streets_data)
    return redirect(url_for('admin_edit', street_id=new_id))

@app.route('/admin/delete_page', methods=['POST'])
def admin_delete_page():
    street_id = request.form['street_id']
    page_index = int(request.form['page_index']) - 1  # Индекс страницы начинается с 1

    streets_data = load_data()
    street = next((s for s in streets_data if s['id'] == street_id), None)

    if street is None:
        return "Street not found", 404

    if 0 <= page_index < len(street['pages']):
        del street['pages'][page_index]
        save_data(streets_data)
    else:
        return "Page not found", 404

    return redirect(url_for('admin_edit', street_id=street_id))

@app.route('/admin/add_page', methods=['POST'])
def admin_add_page():
    street_id = request.form['street_id']

    streets_data = load_data()
    street = next((s for s in streets_data if s['id'] == street_id), None)

    if street is None:
        return "Street not found", 404

    # Создаем новую страницу с пустыми данными
    new_page = {
        "title": "",
        "content": "",
        "photo": ""
    }

    # Добавляем новую страницу в список pages
    street['pages'].append(new_page)

    save_data(streets_data)

    return redirect(url_for('admin_edit', street_id=street_id))

@app.route('/admin/delete_street', methods=['POST'])
def admin_delete_street():
    street_id = request.form['street_id']

    streets_data = load_data()
    street = next((s for s in streets_data if s['id'] == street_id), None)

    if street is None:
        return "Street not found", 404

    streets_data.remove(street)
    save_data(streets_data)

    return redirect(url_for('admin'))

# Добавляем обработчик для статических файлов (изображений)
@app.route('/static/portrets/<filename>')
def serve_portrets(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
