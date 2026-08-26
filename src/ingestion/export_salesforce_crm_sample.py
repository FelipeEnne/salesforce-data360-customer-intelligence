import csv
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "salesforce"
)

IMPORT_FILE = OUTPUT_DIR / "contacts_import.csv"
GROUND_TRUTH_FILE = OUTPUT_DIR / "contacts_ground_truth.csv"

IMPORT_SCHEMA = (
    "External_Customer_Id__c",
    "FirstName",
    "LastName",
    "Email",
    "Phone",
    "Lead_Source__c",
    "Contact_Status__c",
)

GROUND_TRUTH_SCHEMA = (
    "customer_unique_id",
    "quality_profile",
)


QUOTAS = {
    "clean": 600,
    "uppercase_email": 100,
    "formatted_phone": 100,
    "abbreviated_name": 80,
    "missing_email": 50,
    "missing_phone": 40,
    "name_typo": 30,
}


def get_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def fetch_contacts(cursor):
    contacts = []

    for quality_profile, limit in QUOTAS.items():
        cursor.execute(
            """
            SELECT
                customer_unique_id,
                first_name,
                last_name,
                email,
                phone,
                lead_source,
                contact_status,
                quality_profile
            FROM crm.salesforce_contacts
            WHERE quality_profile = %s
            ORDER BY customer_unique_id
            LIMIT %s
            """,
            (
                quality_profile,
                limit,
            ),
        )

        rows = cursor.fetchall()

        if len(rows) != limit:
            raise RuntimeError(
                f"Expected {limit} contacts for "
                f"{quality_profile}, got {len(rows)}"
            )

        contacts.extend(rows)

    return contacts


def write_import_file(contacts):
    """
    CSV usado pelo Salesforce Data Import Wizard.

    utf-8-sig adiciona o BOM UTF-8 para o Salesforce
    reconhecer corretamente caracteres como:
    Antônio, Bárbara, João, etc.
    """
    with IMPORT_FILE.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.writer(file)

        writer.writerow(IMPORT_SCHEMA)

        for row in contacts:
            (
                customer_id,
                first_name,
                last_name,
                email,
                phone,
                lead_source,
                contact_status,
                _quality_profile,
            ) = row

            writer.writerow(
                [
                    customer_id,
                    first_name,
                    last_name,
                    email or "",
                    phone or "",
                    lead_source,
                    contact_status,
                ]
            )


def write_ground_truth_file(contacts):
    """
    Arquivo interno para avaliação.

    Não deve ser importado no Salesforce.
    """
    with GROUND_TRUTH_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.writer(file)

        writer.writerow(GROUND_TRUTH_SCHEMA)

        for row in contacts:
            writer.writerow(
                [
                    row[0],
                    row[7],
                ]
            )


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with get_connection() as conn:
        with conn.cursor() as cursor:
            contacts = fetch_contacts(cursor)

    contacts.sort(
        key=lambda row: row[0]
    )

    write_import_file(contacts)
    write_ground_truth_file(contacts)

    print(
        f"Exported {len(contacts)} Salesforce contacts."
    )

    print(
        f"Import file: {IMPORT_FILE}"
    )

    print(
        f"Ground truth: {GROUND_TRUTH_FILE}"
    )


if __name__ == "__main__":
    main()
