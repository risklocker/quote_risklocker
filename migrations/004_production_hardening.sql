-- Production hardening indexes and compatibility fixes.
-- Run after 001, 002, and 003.

DO $$
DECLARE
    detection_type text;
BEGIN
    SELECT udt_name
    INTO detection_type
    FROM information_schema.columns
    WHERE table_name = 'insurance_companies'
      AND column_name = 'detection_phrases';

    IF detection_type = '_text' THEN
        ALTER TABLE insurance_companies
            ALTER COLUMN detection_phrases TYPE JSONB
            USING to_jsonb(detection_phrases);
    ELSIF detection_type IS DISTINCT FROM 'jsonb' THEN
        ALTER TABLE insurance_companies
            ALTER COLUMN detection_phrases TYPE JSONB
            USING '[]'::jsonb;
    END IF;
END $$;

ALTER TABLE insurance_companies
    ALTER COLUMN detection_phrases SET DEFAULT '[]'::jsonb,
    ALTER COLUMN detection_phrases SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- owner_id is the current creator/owner field for batches.
CREATE INDEX IF NOT EXISTS idx_batches_created_by ON batches(owner_id);
CREATE INDEX IF NOT EXISTS idx_batches_deleted_at ON batches(deleted_at);
CREATE INDEX IF NOT EXISTS idx_batches_purge_after ON batches(purge_after);

CREATE INDEX IF NOT EXISTS idx_uploaded_files_batch_id ON uploaded_files(batch_id);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_deleted_at ON uploaded_files(deleted_at);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_purge_after ON uploaded_files(purge_after);

CREATE INDEX IF NOT EXISTS idx_quotation_drafts_vehicle_no
    ON quotation_drafts ((fields->'vehicle_no'->>'value'));
CREATE INDEX IF NOT EXISTS idx_quotation_drafts_status ON quotation_drafts(status);
CREATE INDEX IF NOT EXISTS idx_quotation_drafts_deleted_at ON quotation_drafts(deleted_at);
CREATE INDEX IF NOT EXISTS idx_quotation_drafts_purge_after ON quotation_drafts(purge_after);

-- draft_id is the current quotation draft foreign key.
CREATE INDEX IF NOT EXISTS idx_generated_pdf_versions_quotation_draft_id
    ON generated_pdf_versions(draft_id);

CREATE INDEX IF NOT EXISTS idx_trash_records_deleted_at ON trash_records(deleted_at);
CREATE INDEX IF NOT EXISTS idx_trash_records_purge_after ON trash_records(purge_after);
