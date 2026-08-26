import csv
import tempfile
import unittest
from pathlib import Path

from src.ingestion import export_data360
from src.ingestion import export_salesforce_crm_sample as salesforce_export


class Data360ExportSchemaTests(unittest.TestCase):
    def test_implemented_data_cloud_exports_keep_required_relationships(self):
        schemas = export_data360.EXPORT_SCHEMAS

        self.assertIn("master_customer_id", schemas["customer_master.csv"])
        self.assertIn("master_customer_id", schemas["orders.csv"])
        self.assertIn("master_customer_id", schemas["support_tickets.csv"])
        self.assertIn(
            "master_customer_id",
            schemas["marketing_interactions.csv"],
        )
        self.assertIn("created_at", schemas["support_tickets.csv"])
        self.assertIn("resolved_at", schemas["support_tickets.csv"])
        self.assertIn("event_at", schemas["marketing_interactions.csv"])

    def test_every_data_cloud_query_has_a_schema_contract(self):
        self.assertEqual(
            set(export_data360.EXPORTS),
            set(export_data360.EXPORT_SCHEMAS),
        )

    def test_header_validation_accepts_exact_order(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "orders.csv"
            expected = export_data360.EXPORT_SCHEMAS["orders.csv"]

            with destination.open("w", newline="", encoding="utf-8") as file:
                csv.writer(file).writerow(expected)

            export_data360.validate_csv_header(destination, expected)

    def test_header_validation_rejects_missing_or_reordered_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "support_tickets.csv"
            expected = export_data360.EXPORT_SCHEMAS["support_tickets.csv"]

            with destination.open("w", newline="", encoding="utf-8") as file:
                csv.writer(file).writerow(reversed(expected))

            with self.assertRaisesRegex(RuntimeError, "Unexpected schema"):
                export_data360.validate_csv_header(destination, expected)

    def test_salesforce_crm_headers_are_explicit_contracts(self):
        self.assertEqual(
            salesforce_export.IMPORT_SCHEMA,
            (
                "External_Customer_Id__c",
                "FirstName",
                "LastName",
                "Email",
                "Phone",
                "Lead_Source__c",
                "Contact_Status__c",
            ),
        )
        self.assertEqual(
            salesforce_export.GROUND_TRUTH_SCHEMA,
            ("customer_unique_id", "quality_profile"),
        )


if __name__ == "__main__":
    unittest.main()
