ALTER TABLE crm.salesforce_contacts
ADD COLUMN IF NOT EXISTS quality_profile TEXT;

CREATE INDEX IF NOT EXISTS idx_salesforce_contacts_quality_profile
    ON crm.salesforce_contacts (quality_profile);
