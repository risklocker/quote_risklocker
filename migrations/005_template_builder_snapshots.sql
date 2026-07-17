-- Template builder and generated PDF snapshot support.
-- Run after 004.

ALTER TABLE generated_pdf_versions
    ADD COLUMN IF NOT EXISTS draft_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS template_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_output_template_configs_status
    ON output_template_configs(status);
