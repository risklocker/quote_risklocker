# Business Rules

## Non-Negotiable Constraints

- Use Supabase/Postgres only for application data; SQLite and local persistent data fallbacks are prohibited.
- Persist source and generated PDFs only in private Supabase Storage. Do not persist PDFs in the repository or application-server directories.
- Never expose service-role keys, backend credentials, storage keys, or provider URLs to the browser.
- Never silently guess an uncertain extracted value. Mark it `Check Needed` for review.
- Generate final PDFs deterministically from reviewed draft data and saved template configuration. Do not use AI-generated layout for final PDFs.
- Do not hardcode fees, roadtax, premium, commission, totals, or other business formulas.
- Preserve Upload -> Check Values -> Generate PDF.

## Review and Extraction

- Native PDF extraction uses text and layout data; enhanced reading is optional staff-facing OCR behavior.
- Store full extraction detail separately from the editable draft. Staff sees concise fields, source text, and friendly hints rather than parser internals.
- Clear values can be populated automatically. Missing, conflicting, or ambiguous required values stay `Check Needed`.
- Batch processing continues if one uploaded file cannot be read.
- Staff-facing copy uses `Review / Edit`, `Please check this value.`, `Enhanced reading`, `PDF Expired`, and the statuses `Ready`, `Check Needed`, `Cannot Read`, and `Generated`.
- Never show OCR, parser, regex, confidence, coordinates, storage keys, provider URLs, or technical stack traces to Staff.

## Templates and Versions

- The default Risklocker Motor Template is locked and copy-only.
- Insurer variations use assets, variables, package configuration, and conditional benefit/add-on cards instead of insurer-specific template forks.
- Generated versions snapshot reviewed draft fields and template configuration; existing versions are never overwritten.

## Roles

- Staff access their own uploads, drafts, history, generation, and trash.
- Managers access Staff records and manage Staff accounts only.
- Admins manage all records, roles, templates, dictionaries, storage, system checks, and purge operations.
- Enforce authorization in backend routes and services.

## Security and Retention

- Uploads are PDF-only, size-limited, validated, quarantined in the OS temporary directory, malware-scanned when required, extraction-limited, and always cleaned up after processing.
- Source and generated PDF binaries expire after the configured retention period, currently 30 days by default. Metadata and reviewed records remain.
- Soft-deleted records stay in Trash for the configured retention period, currently 14 days by default. PDF-binary retention and database-record purging are separate.
- SharePoint/OneDrive archive support is optional, backend-only, and requires Microsoft Entra credentials, checksum verification, and object metadata before activation.
