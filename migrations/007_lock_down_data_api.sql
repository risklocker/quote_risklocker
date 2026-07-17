-- The application uses backend-enforced RBAC and a direct Postgres connection.
-- Do not expose its public-schema tables through the Supabase Data API.

DO $$
DECLARE
    table_name TEXT;
    application_tables TEXT[] := ARRAY[
        'users',
        'insurance_categories',
        'insurance_companies',
        'output_template_configs',
        'benefit_options',
        'field_aliases',
        'vehicle_brands',
        'vehicle_models',
        'batches',
        'document_groups',
        'storage_connections',
        'uploaded_files',
        'extraction_records',
        'quotation_drafts',
        'generated_pdf_versions',
        'trash_records',
        'correction_memory',
        'admin_suggestions',
        'app_settings',
        'audit_events'
    ];
BEGIN
    FOREACH table_name IN ARRAY application_tables LOOP
        IF to_regclass(format('public.%I', table_name)) IS NOT NULL THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', table_name);
            EXECUTE format('REVOKE ALL PRIVILEGES ON TABLE public.%I FROM anon, authenticated', table_name);
        END IF;
    END LOOP;
END $$;
