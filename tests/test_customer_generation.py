import unittest

from src.generators import generate_customer_master as customer_master
from src.generators import generate_salesforce_contacts as salesforce


class CustomerMasterTests(unittest.TestCase):
    def test_normalize_removes_accents_spaces_and_punctuation(self):
        self.assertEqual(
            customer_master.normalize("João da-Silva"),
            "joaodasilva",
        )

    def test_customer_generation_is_deterministic(self):
        first = customer_master.generate_customer(
            "customer-001",
            set(),
        )
        second = customer_master.generate_customer(
            "customer-001",
            set(),
        )

        self.assertEqual(first, second)
        self.assertEqual(first[0], "customer-001")
        self.assertTrue(first[4].endswith("@example.com"))
        self.assertRegex(first[5], r"^\+55\d{11}$")

    def test_generated_phones_are_unique_within_a_run(self):
        used_phones = set()

        first = customer_master.generate_unique_phone(
            "customer-001",
            used_phones,
        )
        second = customer_master.generate_unique_phone(
            "customer-002",
            used_phones,
        )

        self.assertNotEqual(first, second)
        self.assertEqual(used_phones, {first, second})


class SalesforceContactTests(unittest.TestCase):
    def test_salesforce_id_is_stable_and_contact_like(self):
        first = salesforce.salesforce_id("customer-001")
        second = salesforce.salesforce_id("customer-001")

        self.assertEqual(first, second)
        self.assertRegex(first, r"^003[A-F0-9]{15}$")

    def test_phone_formatting(self):
        self.assertEqual(
            salesforce.format_phone("+5511987654321"),
            "(11) 98765-4321",
        )

    def test_contact_transformation_is_deterministic(self):
        source = (
            "customer-001",
            "João",
            "Silva",
            "João Silva",
            "joao.silva@example.com",
            "+5511987654321",
        )

        first = salesforce.transform_customer(source)
        second = salesforce.transform_customer(source)

        self.assertEqual(first, second)
        self.assertEqual(first[1], "customer-001")
        self.assertIn(first[7], salesforce.LEAD_SOURCES)
        self.assertIn(first[8], salesforce.CONTACT_STATUSES)
        self.assertIn(
            first[9],
            {
                "clean",
                "uppercase_email",
                "formatted_phone",
                "abbreviated_name",
                "missing_email",
                "missing_phone",
                "name_typo",
            },
        )


if __name__ == "__main__":
    unittest.main()
