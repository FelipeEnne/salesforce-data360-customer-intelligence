import hashlib
import os
import unicodedata

import psycopg
from dotenv import load_dotenv
from faker import Faker


load_dotenv()

fake = Faker("pt_BR")

AREA_CODES = [
    11, 12, 13, 14, 15, 16, 17, 18, 19,
    21, 22, 24, 27, 28,
    31, 32, 33, 34, 35, 37, 38,
    41, 42, 43, 44, 45, 46,
    47, 48, 49,
    51, 53, 54, 55,
    61, 62, 63, 64, 65, 66, 67,
    68, 69,
    71, 73, 74, 75, 77, 79,
    81, 82, 83, 84, 85, 86, 87, 88, 89,
    91, 92, 93, 94, 95, 96, 97, 98, 99,
]


def get_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def seed_from_customer_id(customer_id: str) -> int:
    digest = hashlib.sha256(customer_id.encode()).hexdigest()
    return int(digest[:8], 16)


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        c for c in value
        if not unicodedata.combining(c)
    )

    return "".join(
        c.lower()
        for c in value
        if c.isalnum()
    )


def generate_unique_phone(
    customer_id: str,
    used_phones: set[str],
) -> str:
    for attempt in range(100):
        value = f"{customer_id}:{attempt}"

        digest = hashlib.sha256(
            value.encode()
        ).hexdigest()

        area_code = AREA_CODES[
            int(digest[:4], 16) % len(AREA_CODES)
        ]

        phone_number = (
            900_000_000
            + int(digest[4:20], 16) % 100_000_000
        )

        phone = f"+55{area_code}{phone_number:09d}"

        if phone not in used_phones:
            used_phones.add(phone)
            return phone

    raise RuntimeError(
        f"Unable to generate unique phone for {customer_id}"
    )


def generate_customer(
    customer_id: str,
    used_phones: set[str],
):
    seed = seed_from_customer_id(customer_id)

    fake.seed_instance(seed)

    first_name = fake.first_name()
    last_name = fake.last_name()
    full_name = f"{first_name} {last_name}"

    suffix = hashlib.sha256(
        customer_id.encode()
    ).hexdigest()[:8]

    email = (
        f"{normalize(first_name)}."
        f"{normalize(last_name)}."
        f"{suffix}@example.com"
    )

    phone_e164 = generate_unique_phone(
        customer_id,
        used_phones,
    )

    birth_date = fake.date_of_birth(
        minimum_age=18,
        maximum_age=75,
    )

    return (
        customer_id,
        first_name,
        last_name,
        full_name,
        email,
        phone_e164,
        birth_date,
    )


def main():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT customer_unique_id
                FROM olist.customers
                WHERE customer_unique_id IS NOT NULL
                ORDER BY customer_unique_id
            """)

            customer_ids = [
                row[0]
                for row in cursor.fetchall()
            ]

            print(
                f"Generating {len(customer_ids)} customers..."
            )

            used_phones = set()

            customers = [
                generate_customer(
                    customer_id,
                    used_phones,
                )
                for customer_id in customer_ids
            ]

            cursor.executemany("""
                INSERT INTO crm.customer_master (
                    customer_unique_id,
                    first_name,
                    last_name,
                    full_name,
                    email,
                    phone_e164,
                    birth_date
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (customer_unique_id)
                DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    full_name = EXCLUDED.full_name,
                    email = EXCLUDED.email,
                    phone_e164 = EXCLUDED.phone_e164,
                    birth_date = EXCLUDED.birth_date
            """, customers)

    print(
        "Customer master generated successfully."
    )


if __name__ == "__main__":
    main()