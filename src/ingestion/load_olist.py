import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "raw" / "olist"

FILES = {
    "olist_customers_dataset.csv": "olist.customers",
    "olist_geolocation_dataset.csv": "olist.geolocation",
    "olist_order_items_dataset.csv": "olist.order_items",
    "olist_order_payments_dataset.csv": "olist.order_payments",
    "olist_order_reviews_dataset.csv": "olist.order_reviews",
    "olist_orders_dataset.csv": "olist.orders",
    "olist_products_dataset.csv": "olist.products",
    "olist_sellers_dataset.csv": "olist.sellers",
    "product_category_name_translation.csv": "olist.product_category_translation",
}


def get_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def load_csv(cursor, file_path: Path, table: str):
    print(f"Loading {file_path.name} -> {table}")

    cursor.execute(f"TRUNCATE TABLE {table}")

    with cursor.copy(
        f"COPY {table} FROM STDIN WITH (FORMAT CSV, HEADER TRUE)"
    ) as copy:
        with file_path.open("r", encoding="utf-8") as file:
            while chunk := file.read(1024 * 1024):
                copy.write(chunk)


def main():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            for filename, table in FILES.items():
                file_path = DATA_DIR / filename

                if not file_path.exists():
                    raise FileNotFoundError(file_path)

                load_csv(cursor, file_path, table)

    print("\nOlist import completed successfully.")


if __name__ == "__main__":
    main()

