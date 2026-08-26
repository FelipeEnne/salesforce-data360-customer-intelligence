import csv
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA360_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "data360"
)

EVALUATION_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "evaluation"
)


EXPORTS = {
    "customer_master.csv": """
        SELECT
            customer_unique_id AS master_customer_id,
            first_name,
            last_name,
            full_name,
            email,
            phone_e164 AS phone,
            birth_date,
            source_system
        FROM crm.customer_master
        ORDER BY customer_unique_id
    """,

    "salesforce_contacts.csv": """
        SELECT
            salesforce_contact_id,
            first_name,
            last_name,
            full_name,
            email,
            phone,
            lead_source,
            contact_status,
            created_at
        FROM crm.salesforce_contacts
        ORDER BY salesforce_contact_id
    """,

    "support_tickets.csv": """
        SELECT
            t.ticket_id,
            cm.customer_unique_id
                AS master_customer_id,
            t.requester_name,
            t.requester_email,
            t.requester_phone,
            t.category,
            t.priority,
            t.status,
            t.channel,
            t.sentiment,
            t.created_at,
            t.resolved_at,
            t.resolution_hours
        FROM support.tickets t
        JOIN crm.customer_master cm
            ON cm.customer_unique_id =
               t.customer_unique_id
        ORDER BY t.ticket_id
    """,

    "marketing_interactions.csv": """
        SELECT
            m.interaction_id,
            cm.customer_unique_id
                AS master_customer_id,
            m.email,
            m.campaign_name,
            m.event_type,
            m.channel,
            m.event_at
        FROM marketing.interactions m
        JOIN crm.customer_master cm
            ON cm.customer_unique_id =
               m.customer_unique_id
        ORDER BY m.interaction_id
    """,

    "web_events.csv": """
        SELECT
            event_id,
            anonymous_id,
            session_id,
            email,
            event_type,
            product_id,
            page_path,
            device_type,
            event_at,
            event_properties::text
                AS event_properties
        FROM web.events
        ORDER BY event_id
    """,

    "orders.csv": """
        SELECT
            o.order_id,
            c.customer_unique_id
                AS master_customer_id,
            o.order_status,
            o.order_purchase_timestamp,
            o.order_approved_at,
            o.order_delivered_customer_date,
            o.order_estimated_delivery_date,

            COALESCE(items.item_value, 0)
                AS item_value,

            COALESCE(items.freight_value, 0)
                AS freight_value,

            COALESCE(payments.payment_value, 0)
                AS payment_value

        FROM olist.orders o

        JOIN olist.customers c
            ON c.customer_id = o.customer_id

        LEFT JOIN (
            SELECT
                order_id,
                SUM(price) AS item_value,
                SUM(freight_value) AS freight_value
            FROM olist.order_items
            GROUP BY order_id
        ) items
            ON items.order_id = o.order_id

        LEFT JOIN (
            SELECT
                order_id,
                SUM(payment_value) AS payment_value
            FROM olist.order_payments
            GROUP BY order_id
        ) payments
            ON payments.order_id = o.order_id

        ORDER BY o.order_id
    """,

    "products.csv": """
        SELECT
            p.product_id,
            p.product_category_name,
            t.product_category_name_english,
            p.product_weight_g,
            p.product_length_cm,
            p.product_height_cm,
            p.product_width_cm
        FROM olist.products p
        LEFT JOIN olist.product_category_translation t
            ON t.product_category_name =
               p.product_category_name
        ORDER BY p.product_id
    """,
}


EXPORT_SCHEMAS = {
    "customer_master.csv": (
        "master_customer_id",
        "first_name",
        "last_name",
        "full_name",
        "email",
        "phone",
        "birth_date",
        "source_system",
    ),
    "salesforce_contacts.csv": (
        "salesforce_contact_id",
        "first_name",
        "last_name",
        "full_name",
        "email",
        "phone",
        "lead_source",
        "contact_status",
        "created_at",
    ),
    "support_tickets.csv": (
        "ticket_id",
        "master_customer_id",
        "requester_name",
        "requester_email",
        "requester_phone",
        "category",
        "priority",
        "status",
        "channel",
        "sentiment",
        "created_at",
        "resolved_at",
        "resolution_hours",
    ),
    "marketing_interactions.csv": (
        "interaction_id",
        "master_customer_id",
        "email",
        "campaign_name",
        "event_type",
        "channel",
        "event_at",
    ),
    "web_events.csv": (
        "event_id",
        "anonymous_id",
        "session_id",
        "email",
        "event_type",
        "product_id",
        "page_path",
        "device_type",
        "event_at",
        "event_properties",
    ),
    "orders.csv": (
        "order_id",
        "master_customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "item_value",
        "freight_value",
        "payment_value",
    ),
    "products.csv": (
        "product_id",
        "product_category_name",
        "product_category_name_english",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ),
}

GROUND_TRUTH_SCHEMA = (
    "customer_unique_id",
    "salesforce_contact_id",
    "example_ticket_id",
    "example_marketing_interaction_id",
    "anonymous_id",
)


GROUND_TRUTH_QUERY = """
    SELECT
        cm.customer_unique_id,

        sf.salesforce_contact_id,

        (
            SELECT t.ticket_id
            FROM support.tickets t
            WHERE t.customer_unique_id =
                  cm.customer_unique_id
            ORDER BY t.ticket_id
            LIMIT 1
        ) AS example_ticket_id,

        (
            SELECT m.interaction_id
            FROM marketing.interactions m
            WHERE m.customer_unique_id =
                  cm.customer_unique_id
            ORDER BY m.interaction_id
            LIMIT 1
        ) AS example_marketing_interaction_id,

        (
            SELECT e.anonymous_id
            FROM web.events e
            WHERE e.customer_unique_id =
                  cm.customer_unique_id
            ORDER BY e.event_at
            LIMIT 1
        ) AS anonymous_id

    FROM crm.customer_master cm

    LEFT JOIN crm.salesforce_contacts sf
        ON sf.customer_unique_id =
           cm.customer_unique_id

    ORDER BY cm.customer_unique_id
"""


def get_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def export_query(cursor, query, destination):
    copy_sql = f"""
        COPY (
            {query}
        )
        TO STDOUT
        WITH (
            FORMAT CSV,
            HEADER TRUE
        )
    """

    with destination.open("wb") as output:
        with cursor.copy(copy_sql) as copy:
            while data := copy.read():
                output.write(data)


def validate_csv_header(destination, expected_columns):
    with destination.open("r", newline="", encoding="utf-8") as input_file:
        actual_columns = tuple(next(csv.reader(input_file)))

    if actual_columns != tuple(expected_columns):
        raise RuntimeError(
            f"Unexpected schema for {destination.name}: "
            f"expected {tuple(expected_columns)}, got {actual_columns}"
        )


def main():
    DATA360_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    EVALUATION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with get_connection() as conn:
        with conn.cursor() as cursor:

            for filename, query in EXPORTS.items():
                destination = DATA360_DIR / filename

                print(f"Exporting {filename}...")

                export_query(
                    cursor,
                    query,
                    destination,
                )
                validate_csv_header(
                    destination,
                    EXPORT_SCHEMAS[filename],
                )

            ground_truth_path = (
                EVALUATION_DIR
                / "identity_ground_truth.csv"
            )

            print(
                "Exporting identity_ground_truth.csv..."
            )

            export_query(
                cursor,
                GROUND_TRUTH_QUERY,
                ground_truth_path,
            )
            validate_csv_header(
                ground_truth_path,
                GROUND_TRUTH_SCHEMA,
            )

    print("\nExport completed successfully.")


if __name__ == "__main__":
    main()
