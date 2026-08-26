# AGENTS.md

## Project Overview

This repository contains a Customer 360 / Customer Intelligence MVP built with:

- Python
- PostgreSQL
- Docker
- Salesforce CRM
- Salesforce Data Cloud / Data 360

The main goal is to demonstrate an end-to-end customer data pipeline including:

1. Source data ingestion
2. Customer master generation
3. Synthetic CRM/support/marketing data
4. Data quality validation
5. Salesforce CRM integration
6. Salesforce Data Cloud ingestion
7. Identity Resolution
8. Customer profile unification
9. Customer analytics and segmentation

Keep the project focused on Data Engineering, Salesforce Data Cloud, and Customer 360.

Do not turn this repository into a generic Full Stack application.

---

## Security Rules

### Secrets

Never read, display, inspect, print, parse, search, copy, modify, or expose:

- `.env`
- `.env.local`
- `.env.production`
- `.env.development`
- credential files
- API tokens
- passwords
- Salesforce credentials
- SSH private keys
- `.pem` files
- access tokens
- refresh tokens
- authentication cookies

Do not run commands such as:

```bash
cat .env
less .env
head .env
tail .env
grep . .env
sed ... .env
awk ... .env
```

---

## Validation Rules

Whenever Python source code, tests, validation tooling, or CI configuration are created, modified, or deleted, run the complete local CI-equivalent suite before considering the work complete:

```bash
make check
```

`make check` includes lint and the full test suite. Do not skip, suppress, or ignore failures. Fix validation errors before completing the task. Documentation-only changes do not require this command unless they also modify validation tooling or CI configuration.
