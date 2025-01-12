# ml_model/Dockerfile

FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей, включая netcat и curl
RUN apt-get update && apt-get install -y netcat-openbsd curl && rm -rf /var/lib/apt/lists/*


# Копирование и установка Python-зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование скриптов, модели и wait-for-it.sh
COPY model_inference.py .
COPY bank_bert.py .
COPY model/ ./model/
COPY wait-for-it.sh ./wait-for-it.sh

# Сделать скрипт исполняемым
RUN chmod +x wait-for-it.sh

# Запуск скрипта, ожидающего Kafka и Redis
CMD ["./wait-for-it.sh", "kafka:9092", "--", "./wait-for-it.sh", "redis:6379", "--", "python", "model_inference.py"]
