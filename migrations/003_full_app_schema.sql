-- Full Risklocker Quotation Converter schema.
-- Postgres/Supabase compatible; existing 001/002 migrations may already create users and insurance_companies.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS insurance_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE insurance_companies ADD COLUMN IF NOT EXISTS source_template_category VARCHAR(120) NOT NULL DEFAULT 'Other / Unknown';

CREATE TABLE IF NOT EXISTS output_template_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    insurance_type VARCHAR(100) NOT NULL DEFAULT 'Motor',
    insurance_company_id UUID REFERENCES insurance_companies(id),
    html_template TEXT NOT NULL DEFAULT '',
    css_template TEXT NOT NULL DEFAULT '',
    static_notes TEXT NOT NULL DEFAULT '',
    editable_fields JSONB NOT NULL DEFAULT '[]'::jsonb,
    fixed_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS benefit_options (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insurance_company_id UUID REFERENCES insurance_companies(id),
    template_id UUID REFERENCES output_template_configs(id),
    label VARCHAR(255) NOT NULL,
    section VARCHAR(120) NOT NULL DEFAULT 'Benefits',
    default_selected BOOLEAN NOT NULL DEFAULT FALSE,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS field_aliases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_name VARCHAR(120) NOT NULL UNIQUE,
    aliases JSONB NOT NULL DEFAULT '[]'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vehicle_brands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(120) NOT NULL UNIQUE,
    aliases JSONB NOT NULL DEFAULT '[]'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vehicle_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id UUID REFERENCES vehicle_brands(id),
    name VARCHAR(160) NOT NULL,
    aliases JSONB NOT NULL DEFAULT '[]'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Uploaded',
    enhanced_reading_requested BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    purge_after TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_batches_owner_id ON batches(owner_id);
CREATE INDEX IF NOT EXISTS idx_batches_status ON batches(status);

CREATE TABLE IF NOT EXISTS document_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id),
    insurance_type VARCHAR(100) NOT NULL DEFAULT 'Motor',
    status VARCHAR(50) NOT NULL DEFAULT 'Uploaded',
    draft_id UUID,
    uploaded_file_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    deleted_at TIMESTAMPTZ,
    purge_after TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_document_groups_owner_id ON document_groups(owner_id);

CREATE TABLE IF NOT EXISTS uploaded_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES batches(id),
    owner_id UUID NOT NULL REFERENCES users(id),
    document_group_id UUID REFERENCES document_groups(id),
    original_filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(120) NOT NULL,
    storage_path VARCHAR(800) NOT NULL,
    size_bytes INTEGER NOT NULL DEFAULT 0,
    insurance_type VARCHAR(100) NOT NULL DEFAULT 'Motor',
    insurance_company_id UUID REFERENCES insurance_companies(id),
    template_id UUID REFERENCES output_template_configs(id),
    status VARCHAR(50) NOT NULL DEFAULT 'Uploaded',
    enhanced_reading BOOLEAN NOT NULL DEFAULT FALSE,
    simple_issue VARCHAR(255),
    deleted_at TIMESTAMPTZ,
    purge_after TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_uploaded_files_batch_id ON uploaded_files(batch_id);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_owner_id ON uploaded_files(owner_id);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_status ON uploaded_files(status);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_company ON uploaded_files(insurance_company_id);

CREATE TABLE IF NOT EXISTS extraction_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uploaded_file_id UUID NOT NULL UNIQUE REFERENCES uploaded_files(id) ON DELETE CASCADE,
    method_summary JSONB NOT NULL DEFAULT '[]'::jsonb,
    raw_text TEXT NOT NULL DEFAULT '',
    ocr_text TEXT NOT NULL DEFAULT '',
    page_text JSONB NOT NULL DEFAULT '[]'::jsonb,
    words JSONB NOT NULL DEFAULT '[]'::jsonb,
    blocks JSONB NOT NULL DEFAULT '[]'::jsonb,
    tables JSONB NOT NULL DEFAULT '[]'::jsonb,
    images JSONB NOT NULL DEFAULT '[]'::jsonb,
    regions JSONB NOT NULL DEFAULT '[]'::jsonb,
    candidates JSONB NOT NULL DEFAULT '{}'::jsonb,
    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    reading_quality VARCHAR(50) NOT NULL DEFAULT 'check_needed',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS quotation_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uploaded_file_id UUID NOT NULL UNIQUE REFERENCES uploaded_files(id) ON DELETE CASCADE,
    owner_id UUID NOT NULL REFERENCES users(id),
    insurance_type VARCHAR(100) NOT NULL DEFAULT 'Motor',
    status VARCHAR(50) NOT NULL DEFAULT 'Check Needed',
    fields JSONB NOT NULL DEFAULT '{}'::jsonb,
    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    reviewed_at TIMESTAMPTZ,
    reviewed_by UUID REFERENCES users(id),
    deleted_at TIMESTAMPTZ,
    purge_after TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quotation_drafts_owner_id ON quotation_drafts(owner_id);
CREATE INDEX IF NOT EXISTS idx_quotation_drafts_status ON quotation_drafts(status);

CREATE TABLE IF NOT EXISTS generated_pdf_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    draft_id UUID NOT NULL REFERENCES quotation_drafts(id) ON DELETE CASCADE,
    uploaded_file_id UUID NOT NULL REFERENCES uploaded_files(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(800) NOT NULL,
    generated_by UUID NOT NULL REFERENCES users(id),
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_generated_pdf_draft_version UNIQUE (draft_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_generated_versions_draft_id ON generated_pdf_versions(draft_id);
CREATE INDEX IF NOT EXISTS idx_generated_versions_uploaded_file_id ON generated_pdf_versions(uploaded_file_id);

CREATE TABLE IF NOT EXISTS trash_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(80) NOT NULL,
    entity_id UUID NOT NULL,
    original_status VARCHAR(50) NOT NULL,
    deleted_by UUID NOT NULL REFERENCES users(id),
    deleted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    purge_after TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trash_records_entity_id ON trash_records(entity_id);
CREATE INDEX IF NOT EXISTS idx_trash_records_purge_after ON trash_records(purge_after);

CREATE TABLE IF NOT EXISTS correction_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    draft_id UUID NOT NULL REFERENCES quotation_drafts(id) ON DELETE CASCADE,
    uploaded_file_id UUID NOT NULL REFERENCES uploaded_files(id) ON DELETE CASCADE,
    field_name VARCHAR(120) NOT NULL,
    original_value TEXT,
    corrected_value TEXT,
    insurance_company_id UUID REFERENCES insurance_companies(id),
    corrected_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_correction_memory_field_name ON correction_memory(field_name);
CREATE INDEX IF NOT EXISTS idx_correction_memory_uploaded_file_id ON correction_memory(uploaded_file_id);

CREATE TABLE IF NOT EXISTS admin_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    suggestion_type VARCHAR(80) NOT NULL,
    field_name VARCHAR(120),
    description TEXT NOT NULL,
    correction_count INTEGER NOT NULL DEFAULT 0,
    examples JSONB NOT NULL DEFAULT '[]'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app_settings (
    key VARCHAR(160) PRIMARY KEY,
    value JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID REFERENCES users(id),
    action VARCHAR(120) NOT NULL,
    entity_type VARCHAR(80) NOT NULL,
    entity_id UUID,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
