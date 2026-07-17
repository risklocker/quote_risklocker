-- Supabase-first PDF storage metadata and optional Microsoft archive destinations.

CREATE TABLE IF NOT EXISTS storage_connections (
    id UUID PRIMARY KEY,
    provider VARCHAR(50) NOT NULL DEFAULT 'microsoft',
    display_name VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(160),
    site_id VARCHAR(500),
    drive_id VARCHAR(500),
    root_item_id VARCHAR(500),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    connected_by UUID REFERENCES users(id),
    last_checked_at TIMESTAMPTZ,
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_storage_connections_status ON storage_connections(status);

ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS storage_provider VARCHAR(50) NOT NULL DEFAULT 'supabase';
ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS storage_bucket VARCHAR(160);
ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS storage_status VARCHAR(50) NOT NULL DEFAULT 'available';
ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS storage_sha256 VARCHAR(64);
ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS storage_etag VARCHAR(255);
ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS storage_stored_at TIMESTAMPTZ;
ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS storage_expires_at TIMESTAMPTZ;
ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS storage_deleted_at TIMESTAMPTZ;
ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS archive_connection_id UUID;
ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS archive_item_id VARCHAR(500);
ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS archive_status VARCHAR(50);
ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS archive_sha256 VARCHAR(64);
ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS security_scan JSONB NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE generated_pdf_versions ADD COLUMN IF NOT EXISTS storage_provider VARCHAR(50) NOT NULL DEFAULT 'supabase';
ALTER TABLE generated_pdf_versions ADD COLUMN IF NOT EXISTS storage_bucket VARCHAR(160);
ALTER TABLE generated_pdf_versions ADD COLUMN IF NOT EXISTS storage_status VARCHAR(50) NOT NULL DEFAULT 'available';
ALTER TABLE generated_pdf_versions ADD COLUMN IF NOT EXISTS storage_sha256 VARCHAR(64);
ALTER TABLE generated_pdf_versions ADD COLUMN IF NOT EXISTS storage_etag VARCHAR(255);
ALTER TABLE generated_pdf_versions ADD COLUMN IF NOT EXISTS storage_stored_at TIMESTAMPTZ;
ALTER TABLE generated_pdf_versions ADD COLUMN IF NOT EXISTS storage_expires_at TIMESTAMPTZ;
ALTER TABLE generated_pdf_versions ADD COLUMN IF NOT EXISTS storage_deleted_at TIMESTAMPTZ;
ALTER TABLE generated_pdf_versions ADD COLUMN IF NOT EXISTS archive_connection_id UUID;
ALTER TABLE generated_pdf_versions ADD COLUMN IF NOT EXISTS archive_item_id VARCHAR(500);
ALTER TABLE generated_pdf_versions ADD COLUMN IF NOT EXISTS archive_status VARCHAR(50);
ALTER TABLE generated_pdf_versions ADD COLUMN IF NOT EXISTS archive_sha256 VARCHAR(64);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_uploaded_files_archive_connection') THEN
        ALTER TABLE uploaded_files
            ADD CONSTRAINT fk_uploaded_files_archive_connection
            FOREIGN KEY (archive_connection_id) REFERENCES storage_connections(id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_generated_versions_archive_connection') THEN
        ALTER TABLE generated_pdf_versions
            ADD CONSTRAINT fk_generated_versions_archive_connection
            FOREIGN KEY (archive_connection_id) REFERENCES storage_connections(id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_uploaded_files_storage_status ON uploaded_files(storage_status);
CREATE INDEX IF NOT EXISTS ix_uploaded_files_storage_expires_at ON uploaded_files(storage_expires_at);
CREATE INDEX IF NOT EXISTS ix_uploaded_files_archive_connection_id ON uploaded_files(archive_connection_id);
CREATE INDEX IF NOT EXISTS ix_generated_versions_storage_status ON generated_pdf_versions(storage_status);
CREATE INDEX IF NOT EXISTS ix_generated_versions_storage_expires_at ON generated_pdf_versions(storage_expires_at);
CREATE INDEX IF NOT EXISTS ix_generated_versions_archive_connection_id ON generated_pdf_versions(archive_connection_id);

-- Existing rows point at legacy local files until the explicit migration command
-- verifies and promotes them. New application writes are always Supabase objects.
UPDATE uploaded_files
SET storage_provider = 'local',
    storage_status = 'available',
    storage_stored_at = COALESCE(storage_stored_at, created_at)
WHERE storage_bucket IS NULL AND storage_path IS NOT NULL;

UPDATE generated_pdf_versions
SET storage_provider = 'local',
    storage_status = 'available',
    storage_stored_at = COALESCE(storage_stored_at, generated_at)
WHERE storage_bucket IS NULL AND storage_path IS NOT NULL;
