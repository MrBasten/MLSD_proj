from flask import Flask, request, jsonify
import pickle
import torch
import re

from bank_bert import BankBert

# Функция очистки текста
def clean_report_text(text):
    """
    Очищает текст от HTML-тегов и специальных символов.
    """
    # Удаление HTML-тегов
    text = re.sub(r'<[^>]+>', '', text)
    # Удаление специальных символов (оставляем только буквы и пробелы)
    text = re.sub(r'[^а-яА-ЯёЁ\s]', '', text)
    # Приведение к нижнему регистру
    text = text.lower()
    # Удаление лишних пробелов
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Загрузка модели
with open("model/model.pkl", "rb") as f:
    bank_bert = pickle.load(f)

# Создание Flask приложения
app = Flask(__name__)

@app.route("/classify", methods=["POST"])
def classify():
    data = request.json
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' in request body"}), 400

    text = data["text"]
    clean_text = clean_report_text(text)
    prediction = bank_bert.eval_net([clean_text])
    return jsonify({"class": prediction[0]})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "OK"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
