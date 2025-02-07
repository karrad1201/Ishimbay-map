import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename

static_folder = os.path.abspath("static")
UPLOAD_FOLDER = os.path.join(static_folder, 'uploads')
app = Flask(__name__, template_folder="templates", static_folder=static_folder)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Создаем папку uploads, если ее нет
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def load_data():
    with open("streets_data.json", 'r', encoding='utf-8') as f:
        streets = json.load(f)
    return streets

def save_data(streets):
    with open("streets_data.json", 'w', encoding='utf-8') as f:
        json.dump(streets, f, ensure_ascii=False, indent=4)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/admin/edit', methods=['GET', 'POST'])
def admin_edit(street_id):
    street_id = int(street_id)
    streets = load_data()
    street = next((s for s in streets if s['id'] == str(street_id)), None)
    if street is None:
        return "Street not found", 404

    if request.method == 'POST':
        if 'img' not in request.files:
            flash('No file part')
            return redirect(url_for('admin_edit', street_id=street_id))
        file = request.files['img']
        if file.filename == '':
            flash('No selected file')
            return redirect(url_for('admin_edit', street_id=street_id))
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # Сохраняем только имя файла, а не путь
            street['img'] = filename
            save_data(streets)
            flash('File successfully uploaded')
            return redirect(url_for('admin_edit', street_id=street_id))
        else:
            flash('File type not allowed')
            return redirect(url_for('admin_edit', street_id=street_id))

    return render_template('admin_edit.html', street=street)

@app.route('/static/uploads/<filename>')
def serve_portrets(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/adm')
def admin():
    streets_data = load_data()
    return render_template('adm.html', streets_data=streets_data)

# Остальной код

@app.route('/uploads/<filename>')
def serve_portrets(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

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
