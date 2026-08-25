import hashlib
import os
from datetime import timedelta

import psycopg
from dotenv import load_dotenv


load_dotenv()


CAMPAIGNS = [
    "Welcome Journey",
    "Summer Sale",
    "Black Friday",
    "Win Back",
    "VIP Rewards",
]

EVENT_TYPES = [
    "email_sent",
    "email_open",
    "email_click",
    "campaign_conversion",
    "unsubscribe",
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


def interaction_id(
    customer_id: str,
    campaign: str,
    event_type: str,
) -> str:
    digest = hash_value(
        f"{customer_id}:{campaign}:{event_type}"
    ).upper()

    return f"MKT-{digest[:14]}"


def transform_email(
    customer_id: str,
    email: str,
):
    bucket = deterministic_int(
        customer_id,
        "marketing-email-quality",
        0,
        99,
    )

    if bucket < 85:
        return email, "clean"

    if bucket < 95:
        return email.upper(), "uppercase_email"

    return None, "missing_email"


def build_event(
    customer_id: str,
    email: str,
    quality_profile: str,
    campaign: str,
    event_type: str,
    base_date,
    offset_hours: int,
):
    return (
        interaction_id(
            customer_id,
            campaign,
            event_type,
        ),
        customer_id,
        email,
        campaign,
        event_type,
        "Email",
        base_date + timedelta(hours=offset_hours),
        quality_profile,
    )


def main():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    cm.customer_unique_id,
                    cm.email,
                    MIN(o.order_purchase_timestamp)
                        AS first_purchase,
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
                    cm.email
                ORDER BY cm.customer_unique_id
            """)

            customers = cursor.fetchall()

            interactions = []

            for (
                customer_id,
                master_email,
                _first_purchase,
                last_purchase,
            ) in customers:

                # Cerca de 70% dos clientes
                # participam de campanhas.
                participation_bucket = deterministic_int(
                    customer_id,
                    "marketing-participation",
                    0,
                    99,
                )

                if participation_bucket >= 70:
                    continue

                campaign = deterministic_choice(
                    customer_id,
                    "campaign",
                    CAMPAIGNS,
                )

                email, quality_profile = transform_email(
                    customer_id,
                    master_email,
                )

                # Mantemos a campanha ancorada
                # em uma data plausível.
                campaign_date = (
                    last_purchase
                    + timedelta(
                        days=deterministic_int(
                            customer_id,
                            "campaign-day-offset",
                            1,
                            45,
                        )
                    )
                )

                # Todos os participantes recebem email.
                interactions.append(
                    build_event(
                        customer_id,
                        email,
                        quality_profile,
                        campaign,
                        "email_sent",
                        campaign_date,
                        0,
                    )
                )

                engagement_bucket = deterministic_int(
                    customer_id,
                    "engagement",
                    0,
                    99,
                )

                # ~45% abrem
                if engagement_bucket < 45:
                    interactions.append(
                        build_event(
                            customer_id,
                            email,
                            quality_profile,
                            campaign,
                            "email_open",
                            campaign_date,
                            deterministic_int(
                                customer_id,
                                "open-hours",
                                1,
                                48,
                            ),
                        )
                    )

                # ~15% clicam
                if engagement_bucket < 15:
                    interactions.append(
                        build_event(
                            customer_id,
                            email,
                            quality_profile,
                            campaign,
                            "email_click",
                            campaign_date,
                            deterministic_int(
                                customer_id,
                                "click-hours",
                                2,
                                72,
                            ),
                        )
                    )

                # ~5% convertem
                if engagement_bucket < 5:
                    interactions.append(
                        build_event(
                            customer_id,
                            email,
                            quality_profile,
                            campaign,
                            "campaign_conversion",
                            campaign_date,
                            deterministic_int(
                                customer_id,
                                "conversion-hours",
                                3,
                                96,
                            ),
                        )
                    )

                unsubscribe_bucket = deterministic_int(
                    customer_id,
                    "unsubscribe",
                    0,
                    99,
                )

                # ~3% fazem unsubscribe
                if unsubscribe_bucket < 3:
                    interactions.append(
                        build_event(
                            customer_id,
                            email,
                            quality_profile,
                            campaign,
                            "unsubscribe",
                            campaign_date,
                            deterministic_int(
                                customer_id,
                                "unsubscribe-hours",
                                1,
                                120,
                            ),
                        )
                    )

            print(
                f"Generating {len(interactions)} "
                "marketing interactions..."
            )

            cursor.executemany("""
                INSERT INTO marketing.interactions (
                    interaction_id,
                    customer_unique_id,
                    email,
                    campaign_name,
                    event_type,
                    channel,
                    event_at,
                    quality_profile
                )
                VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                ON CONFLICT (interaction_id)
                DO UPDATE SET
                    customer_unique_id =
                        EXCLUDED.customer_unique_id,
                    email =
                        EXCLUDED.email,
                    campaign_name =
                        EXCLUDED.campaign_name,
                    event_type =
                        EXCLUDED.event_type,
                    channel =
                        EXCLUDED.channel,
                    event_at =
                        EXCLUDED.event_at,
                    quality_profile =
                        EXCLUDED.quality_profile
            """, interactions)

    print(
        "Marketing interactions generated successfully."
    )


if __name__ == "__main__":
    main()
