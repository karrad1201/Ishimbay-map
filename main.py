from flask import Flask, render_template, request, redirect, url_for
import json
import os
from werkzeug.utils import secure_filename

# Получаем абсолютный путь к папке static
static_folder = os.path.abspath("static")

app = Flask(__name__, static_folder=static_folder)

# Теперь используем static_folder для определения DATA_FILE
DATA_FILE = os.path.join(static_folder, 'streets_data.json')

def load_data():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
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

        # Обновляем атрибуты улицы из данных формы
        street['name'] = request.form['name']
        street['city'] = request.form['city']
        street['class'] = request.form['class']
        street['lat'] = request.form['lat']
        street['lon'] = request.form['lon']
        street['nominatimQuery'] = request.form['nominatimQuery']
        street['panorama'] = request.form['panorama']
        street['type'] = request.form['type']

        # Обновляем данные для каждой страницы
        for i, page in enumerate(street['pages']):
            page['title'] = request.form.get(f'page-{i+1}-title', '')
            page['content'] = request.form.get(f'page-{i+1}-content', '')
            page['photo'] = request.form.get(f'page-{i+1}-photo', '')

        save_data(streets_data)
        return redirect(url_for('admin'))

@app.route('/admin/add', methods=['POST'])
def admin_add():
    streets_data = load_data()
    new_id = get_next_id(streets_data)
    new_street = {
        "city": "",
        "class": "",
        "id": new_id,
        "lat": "",
        "lon": "",
        "name": "Новая улица",
        "nominatimQuery": "",
        "panorama": "",
        "type": "",
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

if __name__ == '__main__':
    app.run(debug=True)
