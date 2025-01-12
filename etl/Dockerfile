# etl/Dockerfile

FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей, включая netcat
RUN apt-get update && apt-get install -y netcat-openbsd curl && rm -rf /var/lib/apt/lists/*


# Копирование и установка Python-зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование скриптов и wait-for-it.sh
COPY etl_service.py .
COPY wait-for-it.sh ./wait-for-it.sh

# Сделать скрипт исполняемым
RUN chmod +x wait-for-it.sh

# Запуск скрипта, ожидающего Kafka, Redis и ML Model
CMD ["./wait-for-it.sh", "kafka:9092", "--", "./wait-for-it.sh", "redis:6379", "--", "./wait-for-it.sh", "ml_model:5000", "--", "python", "etl_service.py"]
