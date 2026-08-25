import unittest
from datetime import datetime, timezone

from src.generators import generate_marketing_interactions as marketing
from src.generators import generate_support_tickets as support
from src.generators import generate_web_events as web


class DeterministicHelpersTests(unittest.TestCase):
    def test_deterministic_values_are_stable_and_in_range(self):
        for module in (marketing, support, web):
            first = module.deterministic_int(
                "customer-001",
                "test-salt",
                10,
                20,
            )
            second = module.deterministic_int(
                "customer-001",
                "test-salt",
                10,
                20,
            )

            self.assertEqual(first, second)
            self.assertGreaterEqual(first, 10)
            self.assertLessEqual(first, 20)

    def test_channel_ids_are_stable(self):
        self.assertEqual(
            support.ticket_id("customer-001", 1),
            support.ticket_id("customer-001", 1),
        )
        self.assertEqual(
            marketing.interaction_id(
                "customer-001",
                "Welcome Journey",
                "email_sent",
            ),
            marketing.interaction_id(
                "customer-001",
                "Welcome Journey",
                "email_sent",
            ),
        )
        self.assertEqual(
            web.make_id("SESSION", "customer-001:1"),
            web.make_id("SESSION", "customer-001:1"),
        )


class WebEventTests(unittest.TestCase):
    def setUp(self):
        self.event_at = datetime(
            2024,
            1,
            1,
            12,
            tzinfo=timezone.utc,
        )

    def test_anonymous_event_omits_known_identity(self):
        event = web.build_event(
            "customer-001",
            "anonymous-001",
            "session-001",
            "product_view",
            1,
            "product-001",
            self.event_at,
            "mobile",
        )

        self.assertIsNone(event[3])
        self.assertIsNone(event[4])
        self.assertEqual(event[7], "/products/product-001")
        self.assertEqual(event[10], "anonymous_only")

    def test_known_event_includes_identity(self):
        event = web.build_event(
            "customer-001",
            "anonymous-001",
            "session-001",
            "purchase",
            2,
            "product-001",
            self.event_at,
            "desktop",
            known=True,
            email="customer@example.com",
            quality_profile="clean",
        )

        self.assertEqual(event[3], "customer-001")
        self.assertEqual(event[4], "customer@example.com")
        self.assertEqual(event[7], "/order-confirmation")
        self.assertEqual(event[10], "clean")


if __name__ == "__main__":
    unittest.main()
