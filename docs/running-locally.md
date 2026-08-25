# Running Locally

## Prerequisites

- Docker with Docker Compose
- Python 3.10 or newer
- Access to the public Olist dataset through Kaggle Hub

Kaggle Hub may require Kaggle credentials. Keep Kaggle and Salesforce credentials, tokens, local `.env` files, generated data, and database dumps out of Git.

## 1. Create the Python environment

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Replace the password placeholder in your local `.env`. Docker Compose requires `POSTGRES_PASSWORD` and reads it from the environment without committing the credential.

## 2. Start PostgreSQL

```bash
docker compose up -d
docker compose ps
```

Files under `sql/schema` are applied automatically when the `postgres_data` volume is created for the first time. They are not reapplied automatically to an existing volume.

## 3. Download and load Olist

```bash
python src/ingestion/download_olist.py
python src/ingestion/load_olist.py
```

The loader truncates each Olist destination table before reloading it.

## 4. Generate the Customer 360 sources

Run the generators in dependency order:

```bash
python src/generators/generate_customer_master.py
python src/generators/generate_salesforce_contacts.py
python src/generators/generate_support_tickets.py
python src/generators/generate_marketing_interactions.py
python src/generators/generate_web_events.py
```

The generators use deterministic rules and upserts, so the same Olist input produces the same generated records.

## 5. Run validation queries

```bash
docker compose exec -T postgres psql -U data360 -d customer360 < sql/analytics/001_validate_olist.sql
docker compose exec -T postgres psql -U data360 -d customer360 < sql/analytics/002_validate_customer_master.sql
docker compose exec -T postgres psql -U data360 -d customer360 < sql/analytics/003_validate_salesforce_contacts.sql
docker compose exec -T postgres psql -U data360 -d customer360 < sql/analytics/004_validate_support_tickets.sql
docker compose exec -T postgres psql -U data360 -d customer360 < sql/analytics/005_validate_marketing_interactions.sql
docker compose exec -T postgres psql -U data360 -d customer360 < sql/analytics/006_validate_web_events.sql
```

## 6. Export for Salesforce CRM and Data Cloud

```bash
python src/ingestion/export_salesforce_crm_sample.py
python src/ingestion/export_data360.py
```

Generated files are written below `data/processed`:

- `salesforce/contacts_import.csv`: Salesforce CRM import sample;
- `salesforce/contacts_ground_truth.csv`: offline evaluation only;
- `data360/*.csv`: source files for Data Cloud ingestion;
- `evaluation/identity_ground_truth.csv`: expected cross-source relationships.

## 7. Run unit tests

The unit tests cover deterministic identity generation, source-specific transformations, web identity states, and Identity Resolution evaluation logic. They do not require PostgreSQL or Salesforce.

```bash
PYTHON_DOTENV_DISABLED=1 python -m unittest discover -s tests -v
```

## 8. Stop PostgreSQL

```bash
docker compose down
```

This preserves the named PostgreSQL volume. Removing that volume also removes the local database and is intentionally not part of the standard workflow.

[Back to README](../README.md)
