import hashlib
import os

import psycopg
from dotenv import load_dotenv


load_dotenv()


LEAD_SOURCES = [
    "Web",
    "Referral",
    "Partner",
    "Event",
    "Organic",
]

CONTACT_STATUSES = [
    "Active",
    "Prospect",
    "Customer",
    "Inactive",
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


def deterministic_index(
    customer_id: str,
    salt: str,
    size: int,
) -> int:
    digest = hash_value(f"{customer_id}:{salt}")
    return int(digest[:8], 16) % size


def salesforce_id(customer_id: str) -> str:
    """
    Generates a stable Salesforce-like Contact ID.

    Real Salesforce Contact IDs usually start with 003.
    This is synthetic and used only in our local environment.
    """
    digest = hash_value(customer_id).upper()

    return f"003{digest[:15]}"


def format_phone(phone: str) -> str:
    """
    Converts:
        +5511987654321

    into:
        (11) 98765-4321
    """
    digits = phone.replace("+55", "")

    ddd = digits[:2]
    first = digits[2:7]
    second = digits[7:]

    return f"({ddd}) {first}-{second}"


def abbreviate_name(
    first_name: str,
    last_name: str,
):
    abbreviated_first = f"{first_name[0]}."

    return (
        abbreviated_first,
        last_name,
        f"{abbreviated_first} {last_name}",
    )


def typo_name(
    first_name: str,
    last_name: str,
):
    if len(first_name) > 3:
        modified_first = first_name[:-1]
    else:
        modified_first = first_name

    return (
        modified_first,
        last_name,
        f"{modified_first} {last_name}",
    )


def transform_customer(row):
    (
        customer_id,
        first_name,
        last_name,
        full_name,
        email,
        phone,
    ) = row

    bucket = deterministic_index(
        customer_id,
        "quality-profile",
        100,
    )

    sf_first_name = first_name
    sf_last_name = last_name
    sf_full_name = full_name
    sf_email = email
    sf_phone = phone

    quality_profile = "clean"

    # 0-59 -> clean record (60%)
    if bucket < 60:
        quality_profile = "clean"

    # 60-69 -> uppercase email (10%)
    elif bucket < 70:
        quality_profile = "uppercase_email"
        sf_email = email.upper()

    # 70-79 -> differently formatted phone (10%)
    elif bucket < 80:
        quality_profile = "formatted_phone"
        sf_phone = format_phone(phone)

    # 80-87 -> abbreviated name (8%)
    elif bucket < 88:
        quality_profile = "abbreviated_name"

        (
            sf_first_name,
            sf_last_name,
            sf_full_name,
        ) = abbreviate_name(
            first_name,
            last_name,
        )

    # 88-92 -> missing email (5%)
    elif bucket < 93:
        quality_profile = "missing_email"
        sf_email = None

    # 93-96 -> missing phone (4%)
    elif bucket < 97:
        quality_profile = "missing_phone"
        sf_phone = None

    # 97-99 -> small name typo (3%)
    else:
        quality_profile = "name_typo"

        (
            sf_first_name,
            sf_last_name,
            sf_full_name,
        ) = typo_name(
            first_name,
            last_name,
        )

    lead_source = LEAD_SOURCES[
        deterministic_index(
            customer_id,
            "lead-source",
            len(LEAD_SOURCES),
        )
    ]

    contact_status = CONTACT_STATUSES[
        deterministic_index(
            customer_id,
            "contact-status",
            len(CONTACT_STATUSES),
        )
    ]

    return (
        salesforce_id(customer_id),
        customer_id,
        sf_first_name,
        sf_last_name,
        sf_full_name,
        sf_email,
        sf_phone,
        lead_source,
        contact_status,
        quality_profile,
    )


def main():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    customer_unique_id,
                    first_name,
                    last_name,
                    full_name,
                    email,
                    phone_e164
                FROM crm.customer_master
                ORDER BY customer_unique_id
            """)

            source_customers = cursor.fetchall()

            print(
                f"Generating {len(source_customers)} "
                "Salesforce contacts..."
            )

            contacts = [
                transform_customer(row)
                for row in source_customers
            ]

            cursor.executemany("""
                INSERT INTO crm.salesforce_contacts (
                    salesforce_contact_id,
                    customer_unique_id,
                    first_name,
                    last_name,
                    full_name,
                    email,
                    phone,
                    lead_source,
                    contact_status,
                    quality_profile
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                ON CONFLICT (salesforce_contact_id)
                DO UPDATE SET
                    customer_unique_id =
                        EXCLUDED.customer_unique_id,
                    first_name =
                        EXCLUDED.first_name,
                    last_name =
                        EXCLUDED.last_name,
                    full_name =
                        EXCLUDED.full_name,
                    email =
                        EXCLUDED.email,
                    phone =
                        EXCLUDED.phone,
                    lead_source =
                        EXCLUDED.lead_source,
                    contact_status =
                        EXCLUDED.contact_status,
                    quality_profile =
                        EXCLUDED.quality_profile
            """, contacts)

    print(
        "Salesforce contacts generated successfully."
    )


if __name__ == "__main__":
    main()