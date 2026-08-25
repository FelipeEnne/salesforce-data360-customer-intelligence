# Identity Resolution

## Ruleset configuration

The ruleset has been configured and executed successfully in Salesforce Data Cloud Developer Edition.

| Setting | Value |
| --- | --- |
| Ruleset name | `Customer 360 MVP` |
| Ruleset ID | `mvp1` |
| Primary DMO | Individual |
| Data Space | `default` |
| Execution status | Completed successfully |

## Match rules

The ruleset uses two independent exact-normalized match rules joined by `OR`. A profile can therefore match through either normalized email or normalized E.164 phone.

```text
Exact Normalized Email
OR
Exact Normalized E.164 Phone
```

| Contact Point | Field | Match method |
| --- | --- | --- |
| Contact Point Email | Email Address | Exact Normalized |
| Contact Point Phone | Formatted E164 Phone Number | Exact Normalized |

Name is intentionally excluded because the synthetic source contains controlled name variations. `External_Customer_Id__c` is also excluded because it is ground truth for evaluation rather than an operational matching attribute.

## Reconciliation rule

The Individual Id reconciliation rule uses Source Priority.

| Priority | Source |
| ---: | --- |
| 1 | Customer Master |
| 2 | `Contact_Home` / Salesforce CRM |

`Ignore empty values` is enabled, preventing an empty value from replacing an available value from the prioritized sources.

## Current execution results

The Data Cloud execution currently reports:

| Metric | Result |
| --- | ---: |
| Source profiles | Approximately 97.12K |
| Unified profiles | Approximately 96.17K |
| Consolidation rate | 1% |
| Unified known profiles | Approximately 96.17K |
| Anonymous unified profiles | 0 |

The current consolidation is consistent with the implemented scope: 96,096 Customer Master records and a 1,000-contact Salesforce CRM sample are the only profile sources loaded into Data Cloud. Records can consolidate when normalized email or normalized phone matches across those sources.

These results confirm that the ruleset executed and produced unified profiles. They do not establish matching accuracy.

## Evaluation boundary

Precision, recall, false-positive counts, and false-negative counts have not yet been calculated. Quantitative evaluation against the exported ground truth is a separate next step.

The ruleset does not use `External_Customer_Id__c` for matching. This preserves that identifier for an independent comparison between expected and resolved relationships.

## Related documentation

- [Data Cloud setup](data-cloud-setup.md)
- [Field mappings](field-mapping.md)
- [Back to README](../README.md)
