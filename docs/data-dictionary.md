# Data Dictionary

This dictionary documents the local PostgreSQL model, generated CSV exports, data lineage, and identity-related fields used by the Customer 360 MVP.

## Classification legend

| Classification | Meaning |
| --- | --- |
| Source | Field loaded unchanged from the public Olist dataset |
| Derived | Field calculated or aggregated from source data |
| Synthetic | Deterministically generated demonstration data |
| Ground truth | Internal identifier used only to evaluate expected relationships |
| Operational | Attribute or identifier exposed to an operational source |

Synthetic identity data is not production personal data. Ground-truth fields must not be used as Identity Resolution shortcuts.

## Schema overview

| Schema | Table | Grain | Origin |
| --- | --- | --- | --- |
| `olist` | `customers` | One row per order-level customer record | Public Olist dataset |
| `olist` | `orders` | One row per order | Public Olist dataset |
| `olist` | `order_items` | One row per item within an order | Public Olist dataset |
| `olist` | `order_payments` | One row per payment attempt/sequence | Public Olist dataset |
| `olist` | `order_reviews` | One row per review record | Public Olist dataset |
| `olist` | `products` | One row per product | Public Olist dataset |
| `olist` | `sellers` | One row per seller | Public Olist dataset |
| `olist` | `geolocation` | One row per geolocation observation | Public Olist dataset |
| `olist` | `product_category_translation` | One row per category translation | Public Olist dataset |
| `crm` | `customer_master` | One row per unique Olist customer | Synthetic enrichment |
| `crm` | `salesforce_contacts` | One CRM-style row per master customer | Synthetic generation |
| `support` | `tickets` | One row per support ticket | Synthetic generation |
| `marketing` | `interactions` | One row per campaign event | Synthetic generation |
| `web` | `events` | One row per web event | Synthetic generation |

## Olist source tables

### `olist.customers`

| Column | PostgreSQL type | Description | Classification |
| --- | --- | --- | --- |
| `customer_id` | `TEXT` | Order-level customer identifier used by orders | Source, operational |
| `customer_unique_id` | `TEXT` | Stable customer identifier across orders | Source, ground truth |
| `customer_zip_code_prefix` | `INTEGER` | Customer ZIP-code prefix | Source |
| `customer_city` | `TEXT` | Customer city | Source |
| `customer_state` | `TEXT` | Customer state code | Source |

### `olist.orders`

| Column | PostgreSQL type | Description | Classification |
| --- | --- | --- | --- |
| `order_id` | `TEXT` | Order identifier | Source, operational |
| `customer_id` | `TEXT` | Reference to `olist.customers.customer_id` | Source, operational |
| `order_status` | `TEXT` | Order lifecycle status | Source |
| `order_purchase_timestamp` | `TIMESTAMP` | Purchase timestamp | Source |
| `order_approved_at` | `TIMESTAMP` | Payment approval timestamp | Source |
| `order_delivered_carrier_date` | `TIMESTAMP` | Carrier handoff timestamp | Source |
| `order_delivered_customer_date` | `TIMESTAMP` | Customer delivery timestamp | Source |
| `order_estimated_delivery_date` | `TIMESTAMP` | Estimated delivery timestamp | Source |

### `olist.order_items`

| Column | PostgreSQL type | Description | Classification |
| --- | --- | --- | --- |
| `order_id` | `TEXT` | Reference to the order | Source, operational |
| `order_item_id` | `INTEGER` | Item sequence within the order | Source |
| `product_id` | `TEXT` | Reference to the product | Source, operational |
| `seller_id` | `TEXT` | Reference to the seller | Source |
| `shipping_limit_date` | `TIMESTAMP` | Seller shipping deadline | Source |
| `price` | `NUMERIC(12,2)` | Item price | Source |
| `freight_value` | `NUMERIC(12,2)` | Item freight value | Source |

### `olist.order_payments`

| Column | PostgreSQL type | Description | Classification |
| --- | --- | --- | --- |
| `order_id` | `TEXT` | Reference to the order | Source, operational |
| `payment_sequential` | `INTEGER` | Payment sequence for the order | Source |
| `payment_type` | `TEXT` | Payment method | Source |
| `payment_installments` | `INTEGER` | Number of installments | Source |
| `payment_value` | `NUMERIC(12,2)` | Payment value | Source |

### `olist.order_reviews`

| Column | PostgreSQL type | Description | Classification |
| --- | --- | --- | --- |
| `review_id` | `TEXT` | Review identifier | Source |
| `order_id` | `TEXT` | Reference to the order | Source, operational |
| `review_score` | `INTEGER` | Review score from 1 to 5 | Source |
| `review_comment_title` | `TEXT` | Optional review title | Source |
| `review_comment_message` | `TEXT` | Optional review text | Source |
| `review_creation_date` | `TIMESTAMP` | Review creation timestamp | Source |
| `review_answer_timestamp` | `TIMESTAMP` | Review answer timestamp | Source |

### `olist.products`

The source dataset uses the original `lenght` spelling in two column names; the local schema preserves it for compatibility.

| Column | PostgreSQL type | Description | Classification |
| --- | --- | --- | --- |
| `product_id` | `TEXT` | Product identifier | Source, operational |
| `product_category_name` | `TEXT` | Product category in Portuguese | Source |
| `product_name_lenght` | `INTEGER` | Product-name character count | Source |
| `product_description_lenght` | `INTEGER` | Description character count | Source |
| `product_photos_qty` | `INTEGER` | Number of product photos | Source |
| `product_weight_g` | `NUMERIC` | Product weight in grams | Source |
| `product_length_cm` | `NUMERIC` | Product length in centimeters | Source |
| `product_height_cm` | `NUMERIC` | Product height in centimeters | Source |
| `product_width_cm` | `NUMERIC` | Product width in centimeters | Source |

### `olist.sellers`

| Column | PostgreSQL type | Description | Classification |
| --- | --- | --- | --- |
| `seller_id` | `TEXT` | Seller identifier | Source |
| `seller_zip_code_prefix` | `INTEGER` | Seller ZIP-code prefix | Source |
| `seller_city` | `TEXT` | Seller city | Source |
| `seller_state` | `TEXT` | Seller state code | Source |

### `olist.geolocation`

| Column | PostgreSQL type | Description | Classification |
| --- | --- | --- | --- |
| `geolocation_zip_code_prefix` | `INTEGER` | ZIP-code prefix | Source |
| `geolocation_lat` | `NUMERIC` | Latitude | Source |
| `geolocation_lng` | `NUMERIC` | Longitude | Source |
| `geolocation_city` | `TEXT` | City | Source |
| `geolocation_state` | `TEXT` | State code | Source |

### `olist.product_category_translation`

| Column | PostgreSQL type | Description | Classification |
| --- | --- | --- | --- |
| `product_category_name` | `TEXT` | Category name in Portuguese | Source |
| `product_category_name_english` | `TEXT` | English category name | Source |

## Customer identity tables

### `crm.customer_master`

| Column | PostgreSQL type | Description | Classification |
| --- | --- | --- | --- |
| `customer_unique_id` | `TEXT` | Stable Olist customer ID and master primary key | Source, ground truth |
| `first_name` | `TEXT` | Generated first name | Synthetic, operational |
| `last_name` | `TEXT` | Generated last name | Synthetic, operational |
| `full_name` | `TEXT` | Generated full name | Synthetic, operational |
| `email` | `TEXT` | Unique generated email address | Synthetic, operational |
| `phone_e164` | `TEXT` | Unique generated E.164 phone number | Synthetic, operational |
| `birth_date` | `DATE` | Generated date of birth | Synthetic, operational |
| `source_system` | `TEXT` | Source label; defaults to `olist_enriched` | Derived |
| `is_synthetic` | `BOOLEAN` | Synthetic-data indicator; defaults to `TRUE` | Derived |
| `created_at` | `TIMESTAMPTZ` | Database insertion timestamp | Derived |

In `customer_master.csv`, `customer_unique_id` is exported as `master_customer_id` and `phone_e164` as `phone`. This CSV is loaded into the Data Cloud `Customer Master` Data Stream.

### `crm.salesforce_contacts`

| Column | PostgreSQL type | Description | Classification |
| --- | --- | --- | --- |
| `salesforce_contact_id` | `TEXT` | Synthetic Salesforce-like Contact ID beginning with `003` | Synthetic, operational |
| `customer_unique_id` | `TEXT` | Expected Customer Master relationship | Ground truth |
| `first_name` | `TEXT` | Contact first name after quality transformation | Synthetic, operational |
| `last_name` | `TEXT` | Contact last name after quality transformation | Synthetic, operational |
| `full_name` | `TEXT` | Contact full name after quality transformation | Synthetic, operational |
| `email` | `TEXT` | Email after quality transformation; may be null | Synthetic, operational |
| `phone` | `TEXT` | Phone after quality transformation; may be null | Synthetic, operational |
| `lead_source` | `TEXT` | Deterministic lead-source category | Synthetic |
| `contact_status` | `TEXT` | Deterministic contact status | Synthetic |
| `created_at` | `TIMESTAMPTZ` | Database insertion timestamp | Derived |
| `quality_profile` | `TEXT` | Transformation applied to the record | Derived, ground truth |

The 1,000-row CRM import exports `customer_unique_id` as `External_Customer_Id__c`. This custom field is retained for evaluation and is not used by Identity Resolution.

## Channel tables

### `support.tickets`

| Column | PostgreSQL type | Description | Classification |
| --- | --- | --- | --- |
| `ticket_id` | `TEXT` | Deterministic ticket identifier | Synthetic, operational |
| `customer_unique_id` | `TEXT` | Expected Customer Master relationship | Ground truth |
| `requester_name` | `TEXT` | Requester name after quality transformation | Synthetic, operational |
| `requester_email` | `TEXT` | Requester email after quality transformation | Synthetic, operational |
| `requester_phone` | `TEXT` | Requester phone after quality transformation | Synthetic, operational |
| `category` | `TEXT` | Ticket category | Synthetic |
| `priority` | `TEXT` | Ticket priority | Synthetic |
| `status` | `TEXT` | Ticket status | Synthetic |
| `channel` | `TEXT` | Email, Chat, Phone, or WhatsApp | Synthetic |
| `sentiment` | `TEXT` | Positive, Neutral, or Negative | Synthetic |
| `created_at` | `TIMESTAMPTZ` | Ticket creation time relative to purchase | Synthetic |
| `resolved_at` | `TIMESTAMPTZ` | Resolution time; null for open tickets | Synthetic |
| `resolution_hours` | `NUMERIC(10,2)` | Hours between creation and resolution | Derived |
| `quality_profile` | `TEXT` | Identity transformation applied | Derived, ground truth |

### `marketing.interactions`

| Column | PostgreSQL type | Description | Classification |
| --- | --- | --- | --- |
| `interaction_id` | `TEXT` | Deterministic campaign-event identifier | Synthetic, operational |
| `customer_unique_id` | `TEXT` | Expected Customer Master relationship | Ground truth |
| `email` | `TEXT` | Campaign email after quality transformation | Synthetic, operational |
| `campaign_name` | `TEXT` | Deterministically assigned campaign | Synthetic |
| `event_type` | `TEXT` | Send, open, click, conversion, or unsubscribe | Synthetic |
| `channel` | `TEXT` | Campaign channel; defaults to Email | Synthetic |
| `event_at` | `TIMESTAMPTZ` | Event timestamp relative to purchase | Synthetic |
| `quality_profile` | `TEXT` | Email transformation applied | Derived, ground truth |

### `web.events`

| Column | PostgreSQL type | Description | Classification |
| --- | --- | --- | --- |
| `event_id` | `TEXT` | Deterministic web-event identifier | Synthetic, operational |
| `anonymous_id` | `TEXT` | Stable anonymous browser/device identifier | Synthetic, operational |
| `session_id` | `TEXT` | Session identifier | Synthetic, operational |
| `customer_unique_id` | `TEXT` | Expected known-customer relationship | Ground truth |
| `email` | `TEXT` | Known email available at identification events | Synthetic, operational |
| `event_type` | `TEXT` | Page view, product view, cart, checkout, or purchase | Synthetic |
| `product_id` | `TEXT` | Product involved in the event | Derived |
| `page_path` | `TEXT` | Generated page path for the event type | Synthetic |
| `device_type` | `TEXT` | Desktop, mobile, or tablet | Synthetic |
| `event_at` | `TIMESTAMPTZ` | Event timestamp relative to purchase | Synthetic |
| `quality_profile` | `TEXT` | Anonymous or known email-quality state | Derived, ground truth |
| `event_properties` | `JSONB` | Extensible event attributes; defaults to an empty object | Synthetic |

## Quality profiles

| Profile | Meaning | Sources |
| --- | --- | --- |
| `clean` | Identity attributes match the Customer Master representation | CRM, Support, Marketing, Web |
| `uppercase_email` | Email address is converted to uppercase | CRM, Support, Marketing, Web |
| `formatted_phone` | Phone number uses a human-readable local format | CRM, Support |
| `abbreviated_name` | First name is abbreviated | CRM, Support |
| `missing_email` | Email address is null | CRM, Support, Marketing, Web |
| `missing_phone` | Phone number is null | CRM, Support |
| `name_typo` | First name contains a deterministic small variation | CRM, Support |
| `anonymous_only` | Web event contains no known customer identity | Web |

## Data Cloud export files

Files under `data/processed` are generated locally and ignored by Git.

| File | Grain | Important fields | Current Data Cloud status |
| --- | --- | --- | --- |
| `data360/customer_master.csv` | One row per master customer | `master_customer_id`, name, email, phone, birth date | Loaded |
| `salesforce/contacts_import.csv` | One row per selected CRM Contact | `External_Customer_Id__c`, name, email, phone | Imported into CRM; native stream loaded |
| `data360/salesforce_contacts.csv` | One row per generated CRM-style contact | Salesforce-like ID, name, email, phone | Not used by current CRM Data Stream |
| `data360/support_tickets.csv` | One row per ticket | `master_customer_id`, requester identity and ticket attributes | Loaded and mapped to Case |
| `data360/marketing_interactions.csv` | One row per campaign event | `master_customer_id`, email, campaign, event type and time | Loaded and mapped to Email Engagement |
| `data360/web_events.csv` | One row per web event | Anonymous/session IDs, email and event attributes | Not loaded |
| `data360/orders.csv` | One row per order | `master_customer_id`, status, timestamps and aggregated values | Loaded and mapped to Sales Order |
| `data360/products.csv` | One row per product | Category translation and dimensions | Not loaded |
| `evaluation/identity_ground_truth.csv` | One row per master customer | Expected cross-source example identifiers | Evaluation only |
| `salesforce/contacts_ground_truth.csv` | One row per imported Contact | Expected master ID and quality profile | Evaluation only |

## Data Cloud field mappings

The field-level mappings for the implemented Customer Master, Salesforce CRM, Orders, Support Tickets, and Marketing Interactions sources are documented separately in [Data Cloud Field Mappings](field-mapping.md).

## Related documentation

- [Data sources](data-sources.md)
- [Data Cloud setup](data-cloud-setup.md)
- [Identity Resolution](identity-resolution.md)
- [Back to README](../README.md)
