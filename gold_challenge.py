import re
import sqlite3
import pandas as pd
from flask import Flask, request, jsonify
from flasgger import Swagger, swag_from
import logging

app = Flask(__name__)

swagger_template = {
    "info": {
        "title": "Dokumentasi sistem API untuk Gold Challenge",
        "version": "1.2.3",
        "description": "Sistem API ini digunakan untuk Gold Challenge Binar"
    },
}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "docs",
            "route": "/docs.json"
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

swagger = Swagger(app, template=swagger_template, config=swagger_config)

# Proses inisialisasi database dengan SQLite3
def init_db():
    try:
        conn = sqlite3.connect('database/gold_challenge.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS texts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_text TEXT,
                cleaned_text TEXT
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error initializing database: {e}")

init_db()

def clean_text(text):
    text = text.lower()  # Penyeragaman ukuran teks (lowercase)
    text = re.sub('[^0-9a-zA-Z]+', ' ', text) # Menghilangkan non-alphanumeric
    text = re.sub(r'@\w+', '', text)  # Menghilangkan username twitter
    text = re.sub(r'\b(rt|RT)\b', '', text)  # Menghilangkan tulisan RT (Retweet)
    text = re.sub(r'\W+', ' ', text)  # Menghilangkan tanda baca
    text = re.sub(r'\s+', ' ', text).strip()  # Menghilangkan whitespace yang tidak diperlukan
    text = re.sub('((www\.[^\s]+)|(https?://[^\s]+)|(https?://[^\s]+))', ' ', text)  # Menghilangkan semua URL yang ada
    text = re.sub(' +', ' ', text)  # Menghilangkan spasi yang berlebihan
    
    return text

# Endpoint untuk hello world
@swag_from("docs/hello_world.yml", methods=["GET"])
@app.route("/", methods=["GET"])
def hello_world():
    json_response = {
        "status_code": 200,
        "description": "Halo, ini merupakan sistem API untuk Gold Challenge",
        "data" : "Hello World",
    }
    return jsonify(json_response)

# Endpoint untuk teks
@swag_from("docs/text.yaml", methods=["GET"])
@app.route("/text", methods=["GET"])
def text_endpoint():
    json_response = {
        "status_code": 200,
        "description": "Ini teks asli, bukan yang palsu",
        "data" : "Halo, ini merupakan endpoint dari teks",
    }
    return jsonify(json_response)

# Endpoint untuk teks yang sudah dibersihkan
@swag_from("docs/text_clean.yaml", methods=["GET"])
@app.route("/text_clean", methods=["GET"])
def text_cleaning():
    original_text = "Halo, apa kabar semua? @username RT"
    cleaned_text = clean_text(original_text)
    json_response = {
        "status_code": 200,
        "description": "Berikut ini merupakan teks yang sudah dibersihkan",
        "data" : cleaned_text
    }
    return jsonify(json_response)

# Endpoint untuk memproses teks dari input user
@swag_from("docs/text_processing.yaml", methods=["POST"])
@app.route('/text-processing', methods=['POST'])
def text_processing():

    text = request.form.get('text')
    cleaned_text = clean_text(text)

    # Penyimpanan ke database
    try:
        conn = sqlite3.connect('database/gold_challenge.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO texts (original_text, cleaned_text) VALUES (?, ?)", (text, cleaned_text))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error saving to database: {e}")
        return jsonify({"status_code": 500, "description": "Internal Server Error", "data": str(e)}), 500

    json_response = {
        'status_code': 200,
        'description': "Berikut ini merupakan teks yang sudah diproses",
        'data_raw': text, # ada perubahan disini
        'data_clean': cleaned_text,
    }
    return jsonify(json_response)

# Endpoint untuk memproses file teks
@swag_from("docs/text_processing_file.yaml", methods=["POST"])
@app.route('/text-processing-file', methods=['POST'])
def text_processing_file():
    file = request.files.getlist('file')[0]
    df = pd.read_csv(file, encoding='ISO-8859-1')
    print(df.columns)

    texts = df['Tweet'].to_list()

    cleaned_texts = [clean_text(text) for text in texts]

    json_response = {
        'status_code': 200,
        'description': "Teks yang sudah diproses",
        'data': cleaned_texts,
    }
    return jsonify(json_response)

if __name__ == '__main__':
    app.run(debug=True)