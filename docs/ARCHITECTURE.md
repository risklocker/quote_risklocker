# Architecture

## System Boundaries

| Layer | Responsibility | Primary location |
| --- | --- | --- |
| Frontend | Staff/admin workflow, authenticated API calls, source-PDF viewing | `frontend/src/` |
| API | HTTP contract, authentication dependency, RBAC entry points | `backend/app/api/` |
| Services | Upload, review, PDF generation, storage retention, admin workflows | `backend/app/services/` |
| Extraction | Native PDF reading, optional enhanced reading, candidate selection, draft mapping | `backend/app/extraction/` |
| Rendering | Deterministic template HTML and PDF generation | `backend/app/rendering/` |
| Data | SQLAlchemy models and ordered Supabase/Postgres migrations | `backend/app/models/`, `migrations/` |
| Storage | Private Supabase Storage adapter and authenticated content delivery | `backend/app/storage/` |

## Core Data Flow

1. An authenticated user uploads PDF bytes to the backend.
2. The backend validates and quarantines the file, runs required security checks, then stores it in private Supabase Storage.
3. The extraction orchestrator produces a hidden extraction record and a reviewable draft.
4. The frontend retrieves the draft, displays the source through an authenticated content endpoint, and saves reviewed values through the API.
5. The backend renders a deterministic PDF from the saved template and reviewed draft, scans it, stores it privately, and records an immutable generated-version snapshot.

## Security Model

- Employee identities are normalized named addresses whose domain is exactly `risklocker.com`; public registration and shared/group identities are not supported.
- New accounts are created in `invited` status and receive a one-time invitation code via the configured backend SMTP relay. The account auto-promotes from `invited` to `active` on the first successful code verification.
- Login uses non-enumerating request-code and verify-code endpoints. One-time codes are HMAC-hashed in Postgres, expire, enforce an attempt limit, and are resend-throttled. Delivery uses only the configured backend SMTP relay.
- Successful verification creates an opaque server-side session. The browser receives only a `Secure`, `HttpOnly`, `SameSite=Lax` cookie; Postgres stores the token hash, an eight-hour sliding idle deadline, a 30-day hard deadline, activity metadata, and revocation state.
- Authenticated dependencies validate the session and current account status on every request, update the rolling idle deadline, and enforce trusted origins for cookie-authenticated mutations. Logout, account disablement, and Admin revocation invalidate server state immediately.
- The backend owns database credentials, authentication hash material, SMTP credentials, and the Supabase service-role key. The frontend stores no authentication credential in browser storage.
- PDF content endpoints use the same session cookie and record authorization checks and support byte ranges for browser viewing.
- In-app notifications are per-recipient records for invitation, role-change, and status-change events. Each notification records event type, title, body, read timestamp, delivery state, and optional audit linkage. The application shell shows an unread count; the Inbox page supports mark-read and mark-all-read actions.
- The FastAPI startup routine verifies the database, ensures the private bucket exists, seeds non-production defaults, and schedules daily storage-retention work.

## Storage Model

- Application data is stored in Supabase/Postgres.
- Source objects use a `source/{year}/{month}/{batch_id}/{uploaded_file_id}.pdf` pattern.
- Generated objects use a `generated/{year}/{month}/{draft_id}/v{version}-{uuid}.pdf` pattern.
- Object expiry removes the binary, not its history, draft, extraction, template, or version snapshot.

## Integration Boundaries

- Supabase Storage is required and private.
- Microsoft 365 archive support is optional and backend-only; it is not a substitute for required Supabase Storage.
- Enhanced reading uses locally available optional tooling; the normal runtime does not depend on external customer directories.

## Current Engineering Baseline

- Authorization is enforced by backend dependencies and RBAC services. The shared frontend shell currently does not filter its Admin navigation by client-side role; this is a user-experience improvement, not an authorization boundary.
- Authentication and employee-account mutation bodies use explicit Pydantic request schemas. Other mutable API bodies still use untyped dictionaries and remain an API-hardening gap.
- `ENHANCED_READING_ENABLED`, `STRICT_NO_GUESSING`, and `AUTO_DOWNLOAD_GENERATED_PDF` are defined in backend configuration but are not consumed by runtime behavior outside configuration loading. Treat them as inactive until they are wired into behavior or removed.
- The application configures CORS but does not configure in-app rate limiting or HTTP security headers. A deployment platform may provide those controls, but that is unverified until the deployment model is documented.
- Dictionary and extraction-settings APIs exist without dedicated frontend pages. Their exposure should be decided as an admin product/UX change rather than inferred from their backend availability.

For endpoint behavior, read [API-CONTRACT.md](API-CONTRACT.md). For configuration and run commands, read [OPERATIONS.md](OPERATIONS.md).
