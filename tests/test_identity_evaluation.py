import unittest

from src.evaluation import evaluate_identity_resolution as evaluation


class IdentityResolutionEvaluationTests(unittest.TestCase):
    def test_classifies_correct_incorrect_and_missing_pairs(self):
        profiles = {
            "unified-001": {
                evaluation.CUSTOMER_MASTER: {"customer-001"},
                evaluation.SALESFORCE_CONTACT: {"customer-001"},
            },
            "unified-002": {
                evaluation.CUSTOMER_MASTER: {"different-customer"},
                evaluation.SALESFORCE_CONTACT: {"customer-002"},
            },
        }

        report = evaluation.evaluate(
            {
                "customer-001",
                "customer-002",
                "customer-003",
            },
            profiles,
            membership_rows=4,
        )

        self.assertEqual(
            report["pair_classification"],
            {
                "true_positives": 1,
                "false_positives": 1,
                "false_negatives": 2,
            },
        )
        self.assertEqual(report["metrics"]["precision"], 0.5)
        self.assertAlmostEqual(
            report["metrics"]["recall"],
            1 / 3,
        )

    def test_overmerged_profile_produces_false_positive_pairs(self):
        profiles = {
            "unified-001": {
                evaluation.CUSTOMER_MASTER: {
                    "customer-001",
                    "customer-002",
                },
                evaluation.SALESFORCE_CONTACT: {
                    "customer-001",
                    "customer-002",
                },
            }
        }

        report = evaluation.evaluate(
            {"customer-001", "customer-002"},
            profiles,
            membership_rows=4,
        )

        self.assertEqual(
            report["pair_classification"],
            {
                "true_positives": 2,
                "false_positives": 2,
                "false_negatives": 0,
            },
        )
        self.assertEqual(report["metrics"]["precision"], 0.5)
        self.assertEqual(report["metrics"]["recall"], 1.0)

    def test_zero_predictions_do_not_divide_by_zero(self):
        profiles = {
            "unified-001": {
                evaluation.CUSTOMER_MASTER: {"customer-001"},
                evaluation.SALESFORCE_CONTACT: set(),
            }
        }

        report = evaluation.evaluate(
            {"customer-001"},
            profiles,
            membership_rows=1,
        )

        self.assertIsNone(report["metrics"]["precision"])
        self.assertEqual(report["metrics"]["recall"], 0.0)
        self.assertIsNone(report["metrics"]["f1_score"])


if __name__ == "__main__":
    unittest.main()
