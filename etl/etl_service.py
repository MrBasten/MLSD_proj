import json
import os
import redis
import requests
from kafka import KafkaConsumer, KafkaProducer

# Параметры
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC_IN = os.environ.get("KAFKA_TOPIC_IN", "reviews_in")
KAFKA_TOPIC_OUT = os.environ.get("KAFKA_TOPIC_OUT", "reviews_classified")
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
ML_SERVICE_URL = os.environ.get("ML_SERVICE_URL", "http://ml_model:5000/classify")

def transform_and_classify(review, producer):
    """
    Трансформирует данные и отправляет их на ML-сервис для классификации.
    """
    try:
        text = review.get("text", "")
        if not text:
            raise ValueError("Missing 'text' in review")

        # Отправка запроса на ML-сервис
        response = requests.post(ML_SERVICE_URL, json={"text": text}, timeout=10)
        if response.status_code != 200:
            raise ValueError(f"ML сервис вернул статус {response.status_code}: {response.text}")

        classification = response.json().get("class", "Unknown")
        review["category"] = classification

        # Отправка классифицированного отзыва в Kafka
        producer.send(KAFKA_TOPIC_OUT, review)
    except Exception as e:
        print(f"Ошибка при обработке отзыва ID {review.get('id')}: {e}")
        # Сохранение отзыва в Redis для повторной попытки
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
        r.rpush("etl_failed_reviews", json.dumps(review))

def main():
    consumer = KafkaConsumer(
        KAFKA_TOPIC_IN,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='etl_service_group'
    )

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8')
    )

    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

    for message in consumer:
        review = message.value
        transform_and_classify(review, producer)

    producer.flush()
    producer.close()
    consumer.close()

if __name__ == "__main__":
    main()
