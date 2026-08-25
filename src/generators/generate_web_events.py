import hashlib
import os
from datetime import timedelta

import psycopg
from dotenv import load_dotenv


load_dotenv()


DEVICE_TYPES = [
    "desktop",
    "mobile",
    "tablet",
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


def make_id(prefix: str, value: str) -> str:
    digest = hash_value(value).upper()
    return f"{prefix}-{digest[:16]}"


def transform_known_email(
    customer_id: str,
    email: str,
):
    bucket = deterministic_int(
        customer_id,
        "web-email-quality",
        0,
        99,
    )

    if bucket < 90:
        return email, "clean"

    if bucket < 97:
        return email.upper(), "uppercase_email"

    return None, "missing_email"


def build_event(
    customer_id,
    anonymous_id,
    session_id,
    event_type,
    event_number,
    product_id,
    event_at,
    device_type,
    known=False,
    email=None,
    quality_profile="anonymous_only",
):
    event_id = make_id(
        "WEB",
        (
            f"{customer_id}:"
            f"{session_id}:"
            f"{event_type}:"
            f"{event_number}"
        ),
    )

    if known:
        event_customer_id = customer_id
        event_email = email
        profile = quality_profile
    else:
        event_customer_id = None
        event_email = None
        profile = "anonymous_only"

    page_paths = {
        "page_view": "/",
        "product_view": f"/products/{product_id}",
        "add_to_cart": "/cart",
        "checkout_started": "/checkout",
        "purchase": "/order-confirmation",
    }

    return (
        event_id,
        anonymous_id,
        session_id,
        event_customer_id,
        event_email,
        event_type,
        product_id,
        page_paths[event_type],
        device_type,
        event_at,
        profile,
    )


def main():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT ON (cm.customer_unique_id)
                    cm.customer_unique_id,
                    cm.email,
                    o.order_purchase_timestamp,
                    oi.product_id
                FROM crm.customer_master cm
                JOIN olist.customers c
                    ON c.customer_unique_id =
                       cm.customer_unique_id
                JOIN olist.orders o
                    ON o.customer_id =
                       c.customer_id
                LEFT JOIN olist.order_items oi
                    ON oi.order_id =
                       o.order_id
                ORDER BY
                    cm.customer_unique_id,
                    o.order_purchase_timestamp DESC,
                    oi.order_item_id
            """)

            customers = cursor.fetchall()

            events = []

            for (
                customer_id,
                master_email,
                purchase_date,
                product_id,
            ) in customers:

                # Aproximadamente 60% dos clientes
                # geram atividade web.
                participation = deterministic_int(
                    customer_id,
                    "web-participation",
                    0,
                    99,
                )

                if participation >= 60:
                    continue

                anonymous_id = make_id(
                    "ANON",
                    customer_id,
                )

                session_id = make_id(
                    "SESSION",
                    f"{customer_id}:1",
                )

                device_type = deterministic_choice(
                    customer_id,
                    "device",
                    DEVICE_TYPES,
                )

                known_email, known_quality = (
                    transform_known_email(
                        customer_id,
                        master_email,
                    )
                )

                # Sessão acontece antes da compra.
                session_start = (
                    purchase_date
                    - timedelta(
                        hours=deterministic_int(
                            customer_id,
                            "session-before-purchase",
                            1,
                            72,
                        )
                    )
                )

                event_number = 1

                # 1. Anônimo entra no site
                events.append(
                    build_event(
                        customer_id,
                        anonymous_id,
                        session_id,
                        "page_view",
                        event_number,
                        product_id,
                        session_start,
                        device_type,
                    )
                )
                event_number += 1

                # 2. Visualiza produto ainda anônimo
                events.append(
                    build_event(
                        customer_id,
                        anonymous_id,
                        session_id,
                        "product_view",
                        event_number,
                        product_id,
                        session_start
                        + timedelta(minutes=3),
                        device_type,
                    )
                )
                event_number += 1

                funnel_bucket = deterministic_int(
                    customer_id,
                    "web-funnel",
                    0,
                    99,
                )

                # ~55% adicionam ao carrinho
                if funnel_bucket < 55:
                    events.append(
                        build_event(
                            customer_id,
                            anonymous_id,
                            session_id,
                            "add_to_cart",
                            event_number,
                            product_id,
                            session_start
                            + timedelta(minutes=8),
                            device_type,
                        )
                    )
                    event_number += 1

                # ~35% chegam ao checkout
                if funnel_bucket < 35:
                    events.append(
                        build_event(
                            customer_id,
                            anonymous_id,
                            session_id,
                            "checkout_started",
                            event_number,
                            product_id,
                            session_start
                            + timedelta(minutes=14),
                            device_type,
                            known=True,
                            email=known_email,
                            quality_profile=known_quality,
                        )
                    )
                    event_number += 1

                # ~20% têm evento de purchase
                if funnel_bucket < 20:
                    events.append(
                        build_event(
                            customer_id,
                            anonymous_id,
                            session_id,
                            "purchase",
                            event_number,
                            product_id,
                            purchase_date,
                            device_type,
                            known=True,
                            email=known_email,
                            quality_profile=known_quality,
                        )
                    )

            print(
                f"Generating {len(events)} web events..."
            )

            cursor.executemany("""
                INSERT INTO web.events (
                    event_id,
                    anonymous_id,
                    session_id,
                    customer_unique_id,
                    email,
                    event_type,
                    product_id,
                    page_path,
                    device_type,
                    event_at,
                    quality_profile
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (event_id)
                DO UPDATE SET
                    anonymous_id =
                        EXCLUDED.anonymous_id,
                    session_id =
                        EXCLUDED.session_id,
                    customer_unique_id =
                        EXCLUDED.customer_unique_id,
                    email =
                        EXCLUDED.email,
                    event_type =
                        EXCLUDED.event_type,
                    product_id =
                        EXCLUDED.product_id,
                    page_path =
                        EXCLUDED.page_path,
                    device_type =
                        EXCLUDED.device_type,
                    event_at =
                        EXCLUDED.event_at,
                    quality_profile =
                        EXCLUDED.quality_profile
            """, events)

    print("Web events generated successfully.")


if __name__ == "__main__":
    main()
