import requests
import json
import time
import os
import redis
from kafka import KafkaProducer

KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC_IN", "reviews_in")
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

def fetch_reviews(max_pages=None, delay=1):
    base_url = "https://www.banki.ru/services/responses/list/ajax/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/112.0.0.0 Safari/537.36"
        )
    }

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8")
    )

    # Подключаемся к Redis
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

    page = 1
    has_more_pages = True

    while has_more_pages:
        params = {
            "page": page,
            "is_countable": "on",
        }

        print(f"--- Парсинг страницы {page} ---")
        try:
            response = requests.get(base_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Ошибка при запросе страницы {page}: {e}")
            # Сохраняем текущую страницу в Redis для повторной попытки позже
            r.rpush("banki_ru_failed_pages", page)
            break

        try:
            data = response.json()
        except ValueError:
            print(f"Не удалось декодировать JSON на странице {page}")
            r.rpush("banki_ru_failed_pages", page)
            break

        reviews = data.get("data", [])
        if not reviews:
            print("Больше отзывов не найдено или вернулся пустой список.")
            break

        for review in reviews:
            # Извлекаем только необходимые поля
            review_id = review.get("id", 0)
            title = review.get("title", "")
            text = review.get("text", "").replace('\n', ' ').replace('\r', ' ')
            grade = review.get("grade", 0) if review.get("grade") is not None else 0
            company_name = review.get("company", {}).get("name", "")
            region = review.get("company", {}).get("region", "")
            category = review.get("category", "")
            date_create = review.get("dateCreate", "1970-01-01 00:00:00")

            # Формируем данные для отправки
            review_data = {
                "id": review_id,
                "title": title,
                "text": text,
                "grade": grade,
                "company_name": company_name,
                "region": region,
                "category": category,
                "date_create": date_create
            }

            try:
                producer.send(KAFKA_TOPIC, review_data)
                print(f"DEBUG: Отправлен отзыв с id={review_id}")
            except Exception as e:
                print(f"Ошибка при отправке сообщения в Kafka: {e}")
                # Сохраняем отзыв в Redis для повторной отправки позже
                r.rpush("banki_ru_failed_reviews", json.dumps(review_data, ensure_ascii=False))

        has_more_pages = data.get("hasMorePages", False)
        if not has_more_pages:
            print("Достигнут конец списка отзывов.")
            break

        if max_pages and page >= max_pages:
            print(f"Достигнуто максимальное количество страниц: {max_pages}")
            break

        page += 1
        time.sleep(delay)

    producer.flush()
    producer.close()
    print("Сбор данных завершён и отправлен в Kafka.")

if __name__ == "__main__":
    max_pages_to_fetch = 5000  # Укажите количество страниц, которое хотите спарсить, или None для всех
    fetch_reviews(max_pages=max_pages_to_fetch, delay=1)
