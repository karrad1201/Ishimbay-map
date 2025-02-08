from flask import Flask, render_template, request, redirect, url_for
import json
import os
from werkzeug.utils import secure_filename

# Получаем абсолютный путь к папке static
static_folder = os.path.abspath("static")

app = Flask(__name__, static_folder=static_folder)

# Теперь используем static_folder для определения DATA_FILE
DATA_FILE = os.path.join(static_folder, 'streets_data.json')

# Папка для хранения загруженных изображений (убедитесь, что она существует!)
UPLOAD_FOLDER = os.path.join(static_folder, 'img')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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


if __name__ == '__main__':
    # Создаем папку для загрузок, если она не существует
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
