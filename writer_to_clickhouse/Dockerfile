# writer_to_clickhouse/Dockerfile

FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей, включая netcat
RUN apt-get update && apt-get install -y netcat-openbsd curl && rm -rf /var/lib/apt/lists/*


# Копирование и установка Python-зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование скриптов и wait-for-it.sh
COPY write_to_ch.py .
COPY wait-for-it.sh ./wait-for-it.sh

# Сделать скрипт исполняемым
RUN chmod +x wait-for-it.sh

# Запуск скрипта, ожидающего Kafka и ClickHouse
CMD ["./wait-for-it.sh", "kafka:9092", "--", "./wait-for-it.sh", "clickhouse:9003", "--", "python", "write_to_ch.py"]
