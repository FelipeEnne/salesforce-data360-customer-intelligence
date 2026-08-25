SHELL := /bin/bash

PYTHON ?= .venv/bin/python
SYSTEM_PYTHON ?= python3

.DEFAULT_GOAL := help
.NOTPARALLEL: pipeline

.PHONY: help setup database status download load generate validate export test pipeline stop

help: ## Show the available commands
	@awk 'BEGIN {FS = ":.*## "; print "Available commands:"} /^[a-zA-Z_-]+:.*## / {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: .venv/bin/python ## Create the virtual environment and install dependencies
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

.venv/bin/python:
	$(SYSTEM_PYTHON) -m venv .venv

database: ## Start PostgreSQL and wait for its health check
	docker compose up -d --wait

status: ## Show the Docker Compose service status
	docker compose ps

download: ## Download the public Olist dataset
	$(PYTHON) src/ingestion/download_olist.py

load: ## Load the Olist CSV files into PostgreSQL
	$(PYTHON) src/ingestion/load_olist.py

generate: ## Generate all Customer 360 sources in dependency order
	$(PYTHON) src/generators/generate_customer_master.py
	$(PYTHON) src/generators/generate_salesforce_contacts.py
	$(PYTHON) src/generators/generate_support_tickets.py
	$(PYTHON) src/generators/generate_marketing_interactions.py
	$(PYTHON) src/generators/generate_web_events.py

validate: ## Run all SQL data-quality checks
	docker compose exec -T postgres psql -U data360 -d customer360 < sql/analytics/001_validate_olist.sql
	docker compose exec -T postgres psql -U data360 -d customer360 < sql/analytics/002_validate_customer_master.sql
	docker compose exec -T postgres psql -U data360 -d customer360 < sql/analytics/003_validate_salesforce_contacts.sql
	docker compose exec -T postgres psql -U data360 -d customer360 < sql/analytics/004_validate_support_tickets.sql
	docker compose exec -T postgres psql -U data360 -d customer360 < sql/analytics/005_validate_marketing_interactions.sql
	docker compose exec -T postgres psql -U data360 -d customer360 < sql/analytics/006_validate_web_events.sql

export: ## Export Salesforce CRM, Data Cloud, and evaluation files
	$(PYTHON) src/ingestion/export_salesforce_crm_sample.py
	$(PYTHON) src/ingestion/export_data360.py

test: ## Run the unit test suite without loading the local .env
	PYTHON_DOTENV_DISABLED=1 $(PYTHON) -m unittest discover -s tests -v

pipeline: ## Run the complete local pipeline
	$(MAKE) database
	$(MAKE) download
	$(MAKE) load
	$(MAKE) generate
	$(MAKE) validate
	$(MAKE) export

stop: ## Stop PostgreSQL while preserving its named volume
	docker compose down
