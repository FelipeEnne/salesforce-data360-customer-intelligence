import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


REQUIRED_MEMBERSHIP_COLUMNS = {
    "unified_profile_id",
    "source_type",
    "source_record_id",
    "ground_truth_customer_id",
}

CUSTOMER_MASTER = "customer_master"
SALESFORCE_CONTACT = "salesforce_contact"
SUPPORTED_SOURCE_TYPES = {
    CUSTOMER_MASTER,
    SALESFORCE_CONTACT,
}

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXPECTED_CONTACTS = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "salesforce"
    / "contacts_ground_truth.csv"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate Salesforce Data Cloud identity resolution "
            "against the CRM import ground truth."
        )
    )

    parser.add_argument(
        "--resolved-memberships",
        required=True,
        type=Path,
        help=(
            "CSV exported from Data Cloud with unified profile "
            "memberships."
        ),
    )
    parser.add_argument(
        "--expected-contacts",
        type=Path,
        default=DEFAULT_EXPECTED_CONTACTS,
        help=(
            "CSV containing customer_unique_id for the Salesforce "
            "Contacts imported into CRM."
        ),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optional destination for the JSON metrics report.",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        help="Optional destination for the Markdown metrics report.",
    )

    return parser.parse_args()


def require_columns(fieldnames, required, file_path):
    available = set(fieldnames or [])
    missing = required - available

    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(
            f"{file_path} is missing required columns: "
            f"{missing_list}"
        )


def load_expected_customer_ids(file_path):
    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        require_columns(
            reader.fieldnames,
            {"customer_unique_id"},
            file_path,
        )

        customer_ids = {
            row["customer_unique_id"].strip()
            for row in reader
            if row["customer_unique_id"].strip()
        }

    if not customer_ids:
        raise ValueError(
            f"{file_path} does not contain any customer_unique_id values"
        )

    return customer_ids


def load_memberships(file_path):
    profiles = defaultdict(
        lambda: {
            CUSTOMER_MASTER: set(),
            SALESFORCE_CONTACT: set(),
        }
    )
    membership_rows = 0

    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        require_columns(
            reader.fieldnames,
            REQUIRED_MEMBERSHIP_COLUMNS,
            file_path,
        )

        for line_number, row in enumerate(reader, start=2):
            unified_profile_id = row["unified_profile_id"].strip()
            source_type = row["source_type"].strip()
            source_record_id = row["source_record_id"].strip()
            ground_truth_customer_id = row[
                "ground_truth_customer_id"
            ].strip()

            if not all(
                (
                    unified_profile_id,
                    source_type,
                    source_record_id,
                    ground_truth_customer_id,
                )
            ):
                raise ValueError(
                    f"{file_path}:{line_number} contains an empty "
                    "required value"
                )

            if source_type not in SUPPORTED_SOURCE_TYPES:
                supported = ", ".join(
                    sorted(SUPPORTED_SOURCE_TYPES)
                )
                raise ValueError(
                    f"{file_path}:{line_number} has unsupported "
                    f"source_type {source_type!r}; expected {supported}"
                )

            profiles[unified_profile_id][source_type].add(
                ground_truth_customer_id
            )
            membership_rows += 1

    if not membership_rows:
        raise ValueError(f"{file_path} does not contain membership rows")

    return profiles, membership_rows


def safe_ratio(numerator, denominator):
    if denominator == 0:
        return None

    return numerator / denominator


def evaluate(expected_customer_ids, profiles, membership_rows):
    predicted_pairs = set()
    evaluated_crm_ids = set()

    for members in profiles.values():
        master_ids = members[CUSTOMER_MASTER]
        crm_ids = (
            members[SALESFORCE_CONTACT]
            & expected_customer_ids
        )

        evaluated_crm_ids.update(crm_ids)

        for master_id in master_ids:
            for crm_id in crm_ids:
                predicted_pairs.add((master_id, crm_id))

    expected_pairs = {
        (customer_id, customer_id)
        for customer_id in expected_customer_ids
    }

    true_positive_pairs = predicted_pairs & expected_pairs
    false_positive_pairs = predicted_pairs - expected_pairs
    false_negative_pairs = expected_pairs - predicted_pairs

    true_positives = len(true_positive_pairs)
    false_positives = len(false_positive_pairs)
    false_negatives = len(false_negative_pairs)

    precision = safe_ratio(
        true_positives,
        true_positives + false_positives,
    )
    recall = safe_ratio(
        true_positives,
        true_positives + false_negatives,
    )

    if precision is None or recall is None or precision + recall == 0:
        f1_score = None
    else:
        f1_score = 2 * precision * recall / (precision + recall)

    return {
        "evaluation_scope": {
            "expected_salesforce_contacts": len(expected_customer_ids),
            "resolved_membership_rows": membership_rows,
            "unified_profiles_in_export": len(profiles),
            "expected_contacts_found_in_export": len(evaluated_crm_ids),
        },
        "pair_classification": {
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
        },
        "metrics": {
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "crm_export_coverage": safe_ratio(
                len(evaluated_crm_ids),
                len(expected_customer_ids),
            ),
        },
    }


def format_metric(value):
    if value is None:
        return "N/A"

    return f"{value:.4f} ({value:.2%})"


def render_markdown(report):
    scope = report["evaluation_scope"]
    pairs = report["pair_classification"]
    metrics = report["metrics"]

    return "\n".join(
        [
            "# Identity Resolution Evaluation",
            "",
            "## Evaluation scope",
            "",
            "| Measure | Value |",
            "| --- | ---: |",
            (
                "| Expected Salesforce Contacts | "
                f"{scope['expected_salesforce_contacts']:,} |"
            ),
            (
                "| Resolved membership rows | "
                f"{scope['resolved_membership_rows']:,} |"
            ),
            (
                "| Unified profiles in export | "
                f"{scope['unified_profiles_in_export']:,} |"
            ),
            (
                "| Expected Contacts found in export | "
                f"{scope['expected_contacts_found_in_export']:,} |"
            ),
            "",
            "## Pair classification",
            "",
            "| Classification | Count |",
            "| --- | ---: |",
            f"| True positives | {pairs['true_positives']:,} |",
            f"| False positives | {pairs['false_positives']:,} |",
            f"| False negatives | {pairs['false_negatives']:,} |",
            "",
            "## Metrics",
            "",
            "| Metric | Result |",
            "| --- | ---: |",
            f"| Precision | {format_metric(metrics['precision'])} |",
            f"| Recall | {format_metric(metrics['recall'])} |",
            f"| F1 score | {format_metric(metrics['f1_score'])} |",
            (
                "| CRM export coverage | "
                f"{format_metric(metrics['crm_export_coverage'])} |"
            ),
            "",
            (
                "Metrics compare Customer Master–Salesforce Contact "
                "pairs within the same Unified Profile against the "
                "CRM import ground truth."
            ),
            "",
        ]
    )


def write_text(file_path, content):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def main():
    args = parse_args()

    expected_customer_ids = load_expected_customer_ids(
        args.expected_contacts
    )
    profiles, membership_rows = load_memberships(
        args.resolved_memberships
    )
    report = evaluate(
        expected_customer_ids,
        profiles,
        membership_rows,
    )

    json_report = json.dumps(
        report,
        indent=2,
        sort_keys=True,
    )
    print(json_report)

    if args.json_output:
        write_text(args.json_output, f"{json_report}\n")

    if args.markdown_output:
        write_text(
            args.markdown_output,
            render_markdown(report),
        )


if __name__ == "__main__":
    main()
