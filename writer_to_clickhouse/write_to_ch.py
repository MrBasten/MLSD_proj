import json
import os
from kafka import KafkaConsumer
from clickhouse_driver import Client
import traceback

KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "reviews_classified")
CLICKHOUSE_HOST = os.environ.get("CLICKHOUSE_HOST", "clickhouse")
CLICKHOUSE_PORT = int(os.environ.get("CLICKHOUSE_PORT", 9000))
CLICKHOUSE_DATABASE = os.environ.get("CLICKHOUSE_DATABASE", "default")

def main():
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='writer_group'
    )

    # Создаем клиент для подключения к ClickHouse
    ch_client = Client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        database=CLICKHOUSE_DATABASE
    )

    # Выводим список существующих таблиц (для отладки)
    try:
        existing_tables = ch_client.execute("SHOW TABLES FROM default")
        print("DEBUG: Existing tables in 'default':", existing_tables)
    except Exception as e:
        print("ERROR while fetching existing tables:", e)
        traceback.print_exc()
        return  # Останавливаем выполнение, если не можем получить таблицы

    for message in consumer:
        review = message.value

        # Извлекаем нужные поля
        review_id = review.get("id", 0)
        title = review.get("title", "")
        text = review.get("text", "")
        grade = review.get("grade", 0) if review.get("grade") is not None else 0
        company_name = review.get("company_name", "")
        region = review.get("region", "")
        category = review.get("category", "")
        date_create = review.get("date_create", "1970-01-01 00:00:00")

        # Пишем в ClickHouse
        insert_query = """
        INSERT INTO default.reviews (id, title, text, grade, company_name, region, category, date_create)
        VALUES
        """
        try:
            ch_client.execute(insert_query, [
                (review_id, title, text, grade, company_name, region, category, date_create)
            ])
            print(f"DEBUG: Inserted review_id={review_id}")
        except Exception as e:
            print("ERROR while inserting into ClickHouse:", e)
            traceback.print_exc()

if __name__ == "__main__":
    main()
