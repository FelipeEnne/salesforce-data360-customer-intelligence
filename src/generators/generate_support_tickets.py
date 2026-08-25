import hashlib
import os
from datetime import timedelta

import psycopg
from dotenv import load_dotenv


load_dotenv()


CATEGORIES = [
    "Delivery",
    "Payment",
    "Product",
    "Refund",
    "Account",
]

PRIORITIES = [
    "Low",
    "Medium",
    "High",
    "Urgent",
]

STATUSES = [
    "Resolved",
    "Resolved",
    "Resolved",
    "Closed",
    "Open",
]

CHANNELS = [
    "Email",
    "Chat",
    "Phone",
    "WhatsApp",
]

SENTIMENTS = [
    "Positive",
    "Neutral",
    "Neutral",
    "Negative",
    "Negative",
]


def get_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def hash_value(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def deterministic_int(
    value: str,
    salt: str,
    minimum: int,
    maximum: int,
) -> int:
    digest = hash_value(f"{value}:{salt}")
    number = int(digest[:12], 16)

    return minimum + (
        number % (maximum - minimum + 1)
    )


def deterministic_choice(
    value: str,
    salt: str,
    options,
):
    index = deterministic_int(
        value,
        salt,
        0,
        len(options) - 1,
    )

    return options[index]


def ticket_id(
    customer_id: str,
    ticket_number: int,
) -> str:
    digest = hash_value(
        f"{customer_id}:ticket:{ticket_number}"
    ).upper()

    return f"TKT-{digest[:12]}"


def format_phone(phone: str) -> str:
    digits = phone.replace("+55", "")

    ddd = digits[:2]
    first = digits[2:7]
    second = digits[7:]

    return f"{ddd} {first}-{second}"


def transform_identity(
    customer_id: str,
    ticket_identifier: str,
    full_name: str,
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
):
    bucket = deterministic_int(
        ticket_identifier,
        "identity-quality",
        0,
        99,
    )

    requester_name = full_name
    requester_email = email
    requester_phone = phone
    quality_profile = "clean"

    # 65%
    if bucket < 65:
        quality_profile = "clean"

    # 10%
    elif bucket < 75:
        quality_profile = "uppercase_email"
        requester_email = email.upper()

    # 10%
    elif bucket < 85:
        quality_profile = "formatted_phone"
        requester_phone = format_phone(phone)

    # 6%
    elif bucket < 91:
        quality_profile = "abbreviated_name"
        requester_name = f"{first_name[0]}. {last_name}"

    # 4%
    elif bucket < 95:
        quality_profile = "missing_email"
        requester_email = None

    # 3%
    elif bucket < 98:
        quality_profile = "missing_phone"
        requester_phone = None

    # 2%
    else:
        quality_profile = "name_typo"

        if len(first_name) > 3:
            requester_name = (
                f"{first_name[:-1]} {last_name}"
            )

    return (
        requester_name,
        requester_email,
        requester_phone,
        quality_profile,
    )


def generate_ticket(
    row,
    ticket_number: int,
):
    (
        customer_id,
        first_name,
        last_name,
        full_name,
        email,
        phone,
        last_purchase,
    ) = row

    identifier = ticket_id(
        customer_id,
        ticket_number,
    )

    (
        requester_name,
        requester_email,
        requester_phone,
        quality_profile,
    ) = transform_identity(
        customer_id,
        identifier,
        full_name,
        first_name,
        last_name,
        email,
        phone,
    )

    category = deterministic_choice(
        identifier,
        "category",
        CATEGORIES,
    )

    priority = deterministic_choice(
        identifier,
        "priority",
        PRIORITIES,
    )

    status = deterministic_choice(
        identifier,
        "status",
        STATUSES,
    )

    channel = deterministic_choice(
        identifier,
        "channel",
        CHANNELS,
    )

    sentiment = deterministic_choice(
        identifier,
        "sentiment",
        SENTIMENTS,
    )

    days_after_purchase = deterministic_int(
        identifier,
        "days-after-purchase",
        1,
        30,
    )

    hours_after_midnight = deterministic_int(
        identifier,
        "created-hour",
        8,
        22,
    )

    created_at = (
        last_purchase
        + timedelta(days=days_after_purchase)
        + timedelta(hours=hours_after_midnight)
    )

    if status in ("Resolved", "Closed"):
        resolution_hours = deterministic_int(
            identifier,
            "resolution-hours",
            1,
            120,
        )

        resolved_at = (
            created_at
            + timedelta(hours=resolution_hours)
        )
    else:
        resolution_hours = None
        resolved_at = None

    return (
        identifier,
        customer_id,
        requester_name,
        requester_email,
        requester_phone,
        category,
        priority,
        status,
        channel,
        sentiment,
        created_at,
        resolved_at,
        resolution_hours,
        quality_profile,
    )


def main():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    cm.customer_unique_id,
                    cm.first_name,
                    cm.last_name,
                    cm.full_name,
                    cm.email,
                    cm.phone_e164,
                    MAX(o.order_purchase_timestamp)
                        AS last_purchase
                FROM crm.customer_master cm
                JOIN olist.customers c
                    ON c.customer_unique_id =
                       cm.customer_unique_id
                JOIN olist.orders o
                    ON o.customer_id =
                       c.customer_id
                GROUP BY
                    cm.customer_unique_id,
                    cm.first_name,
                    cm.last_name,
                    cm.full_name,
                    cm.email,
                    cm.phone_e164
                ORDER BY cm.customer_unique_id
            """)

            customers = cursor.fetchall()

            tickets = []

            for row in customers:
                customer_id = row[0]

                # Aproximadamente 30% dos clientes
                # terão tickets de suporte.
                support_bucket = deterministic_int(
                    customer_id,
                    "has-support-ticket",
                    0,
                    99,
                )

                if support_bucket >= 30:
                    continue

                # Cada cliente selecionado terá
                # entre 1 e 3 tickets.
                ticket_count = deterministic_int(
                    customer_id,
                    "ticket-count",
                    1,
                    3,
                )

                for number in range(
                    1,
                    ticket_count + 1,
                ):
                    tickets.append(
                        generate_ticket(
                            row,
                            number,
                        )
                    )

            print(
                f"Generating {len(tickets)} "
                "support tickets..."
            )

            cursor.executemany("""
                INSERT INTO support.tickets (
                    ticket_id,
                    customer_unique_id,
                    requester_name,
                    requester_email,
                    requester_phone,
                    category,
                    priority,
                    status,
                    channel,
                    sentiment,
                    created_at,
                    resolved_at,
                    resolution_hours,
                    quality_profile
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                ON CONFLICT (ticket_id)
                DO UPDATE SET
                    customer_unique_id =
                        EXCLUDED.customer_unique_id,
                    requester_name =
                        EXCLUDED.requester_name,
                    requester_email =
                        EXCLUDED.requester_email,
                    requester_phone =
                        EXCLUDED.requester_phone,
                    category =
                        EXCLUDED.category,
                    priority =
                        EXCLUDED.priority,
                    status =
                        EXCLUDED.status,
                    channel =
                        EXCLUDED.channel,
                    sentiment =
                        EXCLUDED.sentiment,
                    created_at =
                        EXCLUDED.created_at,
                    resolved_at =
                        EXCLUDED.resolved_at,
                    resolution_hours =
                        EXCLUDED.resolution_hours,
                    quality_profile =
                        EXCLUDED.quality_profile
            """, tickets)

    print(
        "Support tickets generated successfully."
    )


if __name__ == "__main__":
    main()
