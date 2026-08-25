# Identity Resolution Evaluation

## Status

The quantitative evaluator is implemented, but no metrics are reported yet because the repository does not contain a detailed export of Data Cloud Unified Profile memberships.

Aggregated Data Cloud counts such as source profiles, unified profiles, and consolidation rate are not sufficient to calculate precision or recall. Evaluation requires the source records assigned to each Unified Profile.

## Evaluation scope

The current Data Cloud MVP contains Customer Master and a 1,000-contact Salesforce CRM sample. Each imported Contact has an `External_Customer_Id__c` value that identifies its expected Customer Master record. This field is ground truth only and is not used by the Identity Resolution ruleset.

The evaluator measures Customer Master–Salesforce Contact pairs:

- **True positive:** the CRM Contact and its expected Customer Master belong to the same Unified Profile.
- **False positive:** the CRM Contact is grouped with a different Customer Master.
- **False negative:** the expected CRM Contact–Customer Master pair is not present in the same Unified Profile.
- **Precision:** true positives divided by all predicted pairs.
- **Recall:** true positives divided by all expected pairs.
- **F1 score:** harmonic mean of precision and recall.
- **CRM export coverage:** imported Contacts found in the detailed Data Cloud export.

If a Unified Profile contains multiple Customer Master or CRM ground-truth IDs, the evaluator creates the cross-product of those IDs. This makes over-merged profiles visible as false-positive pairs.

## Required Data Cloud export

Create a CSV containing one row per source record assigned to a Unified Profile. Normalize the exported columns to this contract before running the evaluator:

| Column | Description |
| --- | --- |
| `unified_profile_id` | Data Cloud Unified Profile identifier |
| `source_type` | `customer_master` or `salesforce_contact` |
| `source_record_id` | Original DLO/source record identifier |
| `ground_truth_customer_id` | Customer Master ID or CRM `External_Customer_Id__c` |

Example structure using fictional values:

```csv
unified_profile_id,source_type,source_record_id,ground_truth_customer_id
UP-001,customer_master,MASTER-001,CUSTOMER-001
UP-001,salesforce_contact,CONTACT-001,CUSTOMER-001
```

Store the normalized file locally, for example at:

```text
data/processed/evaluation/data_cloud_resolved_memberships.csv
```

The `data/processed` directory is ignored by Git. The detailed export should remain local.

## Run the evaluation

```bash
python src/evaluation/evaluate_identity_resolution.py \
  --resolved-memberships data/processed/evaluation/data_cloud_resolved_memberships.csv \
  --json-output data/processed/evaluation/identity_metrics.json \
  --markdown-output data/processed/evaluation/identity_metrics.md
```

By default, expected CRM identities are read from:

```text
data/processed/salesforce/contacts_ground_truth.csv
```

Use `--expected-contacts` to provide another file with a `customer_unique_id` column.

## Guardrails

The evaluator fails when required columns or values are missing, when an unsupported source type is present, or when an input contains no usable records. It does not infer metrics from aggregate profile counts.

Do not publish precision, recall, or F1 results until the detailed membership export has been generated and evaluated.

## Related documentation

- [Identity Resolution configuration](identity-resolution.md)
- [Data Cloud setup](data-cloud-setup.md)
- [Back to README](../README.md)
