# Risklocker Finalization Prompts

Use these prompts in order. Before every prompt,

read `docs/START-HERE.md`, then load only the routed documents and implementation files needed for that prompt. Treat every prompt as a complete vertical slice: backend, frontend, database migration, API contract, tests, verification, and necessary documentation updates. Do not make speculative business rules, hard-code rates or fees, expose secrets, persist PDFs locally, or guess uncertain extracted values.

**Skill loading is mandatory for every prompt.** Consult [docs/SKILLS.md](docs/SKILLS.md) and load the project-local skills that match the work. In particular, the `risklocker-verification` skill MUST be loaded before the verification step of any prompt; a prompt is not complete until the backend starts against the real `.env` (see the verification rule in SKILLS.md). When a prompt lists external "Required skills", the project-local skills with the same coverage take precedence and should be loaded first.

## 1. Internal passwordless authentication and secure sessions

read ​docs/START-HERE.md​, then load only the routed documents and implementation files needed for that prompt. Treat every prompt as a complete vertical slice: backend, frontend, database migration, API contract, tests, verification, and necessary documentation updates. Do not make speculative business rules, hard-code rates or fees, expose secrets, persist PDFs locally, or guess uncertain extracted values.

**Objective:** Replace the current password and browser-token login with a secure passwordless employee login for Risklocker staff.

**Required scope:**

- Accept employee accounts only when their normalized address ends exactly in `@risklocker.com`. Reject all other domains everywhere accounts are created, updated, seeded, or authenticated.
- Do not allow public registration. Shared or group addresses are not application identities; only named employee accounts may sign in.
- Replace password sign-in and `localStorage` bearer-token storage with a request-code and verify-code flow. Send one-time codes only through the configured backend SMTP relay.
- Create server-side, revocable sessions. Use secure HttpOnly cookies, a rolling eight-hour active-session window, and a 30-day inactivity limit. Logout, account disablement, and an Admin revoke must invalidate access immediately.
- Store verification codes securely as hashes, with expiry, attempt limits, resend throttling, audit events, and non-enumerating request responses.
- Refine the login screen into a simple, interactive Risklocker entry point. Include a small “How to use” control that tells staff to check **the email provided** for the login confirmation code; do not state a domain in that instruction.

**Constraints:** Preserve backend-enforced RBAC; never expose SMTP credentials or service-role keys to the frontend. Do not keep a JWT or session secret in `localStorage` or `sessionStorage`.

**Required skills:** `supabase`, `vercel:nextjs`, `frontend-design`, and `vercel-react-best-practices`.

**Verification:** Add unit and HTTP tests for allowed/rejected domains, code expiry and throttling, login, logout, revoked/disabled accounts, 8-hour rolling activity, and 30-day inactivity. Verify the frontend no longer stores authentication tokens in browser storage.

**Documentation:** Update `MEMORY.md`, `ARCHITECTURE.md`, `API-CONTRACT.md`, `OPERATIONS.md`, `TESTING.md`, and the code map if routes/schema/environment variables change.

## 2. SMTP relay, invitations, role notices, and in-app inbox

read ​docs/START-HERE.md​, then load only the routed documents and implementation files needed for that prompt. Treat every prompt as a complete vertical slice: backend, frontend, database migration, API contract, tests, verification, and necessary documentation updates. Do not make speculative business rules, hard-code rates or fees, expose secrets, persist PDFs locally, or guess uncertain extracted values.

**Objective:** Deliver real internal account messages through the approved SMTP relay and make the same messages visible in the application.

**Required scope:**

- Add backend-only SMTP relay configuration, connection validation, delivery failure handling, and an Admin-only test-message action addressed only to the current Admin’s own employee email.
- When an Admin creates an employee account, create an invited/pending account and send the invitation/one-time-code email.
- When an Admin changes a role or account status, send a clear internal email and create a persistent in-app notification.
- Implement notification records with event type, recipient, title, body, read timestamp, delivery state, created timestamp, and audit linkage.
- Add an unread indicator in the application shell and an Inbox page with unread/read states and mark-read actions.
- Limit v1 notifications to invitations and role/account-status events. Do not add staff-to-staff chat, marketing, or customer messaging.

**Constraints:** Delivery must use the backend SMTP relay only. Do not add shared/group mailbox login or configure non-employee recipients.

**Required skills:** `supabase`, `vercel:nextjs`, `frontend-design`, and `vercel-react-best-practices`.

**Verification:** Test invitation delivery requests, role/status notifications, delivery-failure recording, recipient isolation, unread counts, marking read, and RBAC for Admin-only mail test actions.

**Documentation:** Update `MEMORY.md`, `ARCHITECTURE.md`, `API-CONTRACT.md`, `OPERATIONS.md`, `TESTING.md`, and the code map when required.

## 3. Role-aware shell and complete logout flow

read ​docs/START-HERE.md​, then load only the routed documents and implementation files needed for that prompt. Treat every prompt as a complete vertical slice: backend, frontend, database migration, API contract, tests, verification, and necessary documentation updates. Do not make speculative business rules, hard-code rates or fees, expose secrets, persist PDFs locally, or guess uncertain extracted values.

**Objective:** Make navigation, account state, and logout coherent from first sign-in through session expiry.

**Required scope:**

- Load the current session/user safely on application start and show only navigation available to that role. Keep backend RBAC authoritative even when UI navigation is hidden.
- Hide Admin navigation and Admin-only actions from Staff and Manager users according to their permitted scope.
- Add a clear profile/session area with employee email, role, Inbox access, and sign out.
- Handle expired, revoked, disabled, and malformed sessions consistently: clear local UI state, explain what happened, and return the user to login without loops.
- Preserve the existing quiet Risklocker visual system while improving layout, responsive behavior, focus states, and empty/loading/error states.

**Constraints:** Do not restore bearer-token storage. Do not rely on client-side role checks for authorization.

**Required skills:** `vercel:nextjs`, `frontend-design`, and `vercel-react-best-practices`.

**Verification:** Browser and component tests must cover each role’s navigation, logout, session expiry, revocation, and inaccessible-route behavior.

**Documentation:** Update `MEMORY.md`, `DESIGN-SYSTEM.md`, `API-CONTRACT.md`, and `TESTING.md` when applicable.

## 4. Dashboard readiness, upload contract, and recent quotation jobs

read ​docs/START-HERE.md​, then load only the routed documents and implementation files needed for that prompt. Treat every prompt as a complete vertical slice: backend, frontend, database migration, API contract, tests, verification, and necessary documentation updates. Do not make speculative business rules, hard-code rates or fees, expose secrets, persist PDFs locally, or guess uncertain extracted values.

**Objective:** Turn the first signed-in screen into a trustworthy dashboard for system readiness and quotation uploads.

**Required scope:**

- Make Dashboard the first signed-in route. It must show a real readiness check before upload: frontend-to-API reachability, backend availability, database query, private Supabase storage access, and required PDF processing dependencies.
- Add an authenticated, staff-safe readiness endpoint that exposes no secrets and reports actual check time, status, and actionable failure messages.
- Disable upload when a required readiness check fails. Support manual refresh before file selection and again before submission.
- Align all upload copy, file pickers, validation, and server limits to PDF-only behavior and the configured true maximum size. Remove image and unsupported 50 MB claims.
- Create a quotation job for every upload. Use an automatic timestamped name based on uploaded filename(s), let the owner rename it, and show the owner’s five newest jobs in the side panel. “More” must go to History.
- Display real elapsed upload/processing duration from observed browser/server timestamps. Do not invent progress stages, percentages, or ETAs.

**Constraints:** Keep the staff workflow Upload -> Check Values -> Generate PDF. PDFs remain private Supabase Storage objects only.

**Required skills:** `supabase`, `vercel:nextjs`, `frontend-design`, and `vercel-react-best-practices`.

**Verification:** Test readiness failure/success paths, blocked upload, PDF-only validation, configured size limit, job creation/rename, recent-job owner isolation, and actual duration display.

**Documentation:** Update `MEMORY.md`, `ARCHITECTURE.md`, `API-CONTRACT.md`, `DESIGN-SYSTEM.md`, `TESTING.md`, `OPERATIONS.md`, and the code map when required.

## 5. Configurable extraction-field registry and two-column datasets

read ​docs/START-HERE.md​, then load only the routed documents and implementation files needed for that prompt. Treat every prompt as a complete vertical slice: backend, frontend, database migration, API contract, tests, verification, and necessary documentation updates. Do not make speculative business rules, hard-code rates or fees, expose secrets, persist PDFs locally, or guess uncertain extracted values.

**Objective:** Make extraction fields and accepted values administratively controlled rather than dependent on hard-coded aliases and assumptions.

**Required scope:**

- Create an Admin-managed field registry for existing and required fields, including coverage type, cover period, car model, NCD, coverage amount, premium, road tax, runner fee, total premium, add-ons, and existing supported values.
- Each field must have stable key, label, data type, active status, extraction/search status, review visibility, and validation metadata.
- When a field is inactive, new uploads must not search, normalize, validate, or show it in review. Preserve historical draft fields and existing template references unchanged.
- Add per-field Excel/CSV import/export using exactly two data columns: `accepted_variant` and `canonical_value`. Provide preview, row-level validation, duplicate detection, activation, edit, deletion, and import audit data.
- Use active datasets after OCR to normalize matching variants only. Ambiguous, missing, unsupported, or conflicting values must stay `check_needed` with evidence; never guess.
- Migrate current aliases and the approved NCD value set into this model. Preserve the current API behavior until typed replacement endpoints are ready.

**Constraints:** Do not silently coerce values outside an approved dataset. Do not add a generic “AI chooses the value” fallback.

**Required skills:** `supabase`, `supabase-postgres-best-practices`, and `vercel:nextjs`.

**Verification:** Test activation/deactivation, two-column import errors, canonical matching, ambiguity, NCD allowed-value enforcement, historical draft compatibility, and Admin RBAC.

**Documentation:** Update `MEMORY.md`, `BUSINESS-RULES.md`, `ARCHITECTURE.md`, `API-CONTRACT.md`, `TESTING.md`, and the code map when required.

## 6. Vehicle brands/models and approved road-tax reference data

read ​docs/START-HERE.md​, then load only the routed documents and implementation files needed for that prompt. Treat every prompt as a complete vertical slice: backend, frontend, database migration, API contract, tests, verification, and necessary documentation updates. Do not make speculative business rules, hard-code rates or fees, expose secrets, persist PDFs locally, or guess uncertain extracted values.

**Objective:** Replace hard-coded vehicle detection and road-tax assumptions with auditable Admin-approved reference data.

**Required scope:**

- Extend the existing vehicle-brand and vehicle-model data model with bulk import, export, aliases, active status, brand-to-model relationships, duplicate handling, and import audit information.
- Remove extraction dependence on hard-coded vehicle brand/model lists. Use only active approved records and their aliases for normalization.
- Add an effective-dated road-tax reference table that distinguishes Peninsular Malaysia, Sabah, and Sarawak and can support all vehicle classes.
- Every road-tax rule must record jurisdiction, vehicle class, optional subclass/fuel criteria, inclusive engine-CC range, annual rate, source reference, effective dates, active status, and importer/audit information.
- When exactly one active approved rule matches the draft jurisdiction, vehicle class, and engine CC, always replace the extracted road-tax value with the approved rate and show its source in review. If no unique match exists, mark road tax for review rather than calculating or guessing.
- Supply import templates and validate that overlapping active rules cannot produce ambiguous automatic matches.

**Constraints:** Rates are Admin-imported approved data only. Do not seed unverified public rates or hard-code any road-tax formula.

**Required skills:** `supabase`, `supabase-postgres-best-practices`, and `vercel:nextjs`.

**Verification:** Test brand/model normalization, inactive records, each jurisdiction, every vehicle-class matching path, overlapping rules, no-match behavior, effective-date behavior, and automatic road-tax replacement.

**Documentation:** Update `MEMORY.md`, `BUSINESS-RULES.md`, `ARCHITECTURE.md`, `API-CONTRACT.md`, `OPERATIONS.md`, `TESTING.md`, and the code map when required.

## 7. Extraction quality, review, and deterministic generation

read ​docs/START-HERE.md​, then load only the routed documents and implementation files needed for that prompt. Treat every prompt as a complete vertical slice: backend, frontend, database migration, API contract, tests, verification, and necessary documentation updates. Do not make speculative business rules, hard-code rates or fees, expose secrets, persist PDFs locally, or guess uncertain extracted values.

**Objective:** Make the Check Values stage transparent, dataset-aware, and safe before deterministic PDF generation.

**Required scope:**

- Integrate active field datasets, vehicle records, insurer detection, and approved road-tax rules into candidate selection and review status.
- For every reviewable field, show value, source evidence, confidence/status, and whether it came from source text, approved normalization, or a road-tax rule.
- Keep uncertain, conflicting, missing, or unsupported values in `check_needed`; preserve manual correction and correction-memory behavior.
- Ensure company/template choices and benefits/add-ons are captured in the reviewed draft snapshot.
- Generate final PDFs deterministically from reviewed draft data and saved template configuration only. Preserve source/download permissions, version snapshots, and private storage retention.

**Constraints:** Never generate an AI-designed final PDF or silently accept uncertain extraction. Keep Upload -> Check Values -> Generate PDF unchanged.

**Required skills:** `supabase`, `vercel:nextjs`, and `vercel-react-best-practices`.

**Verification:** Extend extraction regressions for datasets, vehicle matching, ambiguous candidates, review blocking, correction history, snapshots, and deterministic repeat generation.

**Documentation:** Update `MEMORY.md`, `BUSINESS-RULES.md`, `ARCHITECTURE.md`, `API-CONTRACT.md`, and `TESTING.md` when applicable.

## 8. Company-centered catalog for insurers, specials, and add-ons

read ​docs/START-HERE.md​, then load only the routed documents and implementation files needed for that prompt. Treat every prompt as a complete vertical slice: backend, frontend, database migration, API contract, tests, verification, and necessary documentation updates. Do not make speculative business rules, hard-code rates or fees, expose secrets, persist PDFs locally, or guess uncertain extracted values.

**Objective:** Reorganize insurer configuration around companies rather than mixed admin pages and template packages.

**Required scope:**

- Rebuild the Company Admin area around insurer lifecycle: create, edit, activate/deactivate, detection phrases, logo, default template, and company-scoped catalog assignments.
- Support the requested insurers and future insurers without code changes: QBE, AmGen, Liberty, STMB, Tune, Etiqa, Lonpac, Sompo, and any Admin-created company.
- Replace the mixed benefit model with a reusable global catalog containing explicit `special` and `addon` item types, title, description, image/logo, visual style, active status, and audit history.
- Support many-to-many company assignments. Provide company filters that can show items shared by selected insurers.
- Specials are automatically included for their company. Add-ons are available separately for later staff selection.
- Add only clearly labelled inactive draft examples until approved insurer benefit content is entered by an Admin. Do not represent invented benefits as actual coverage.

**Constraints:** Company disablement must prevent new selection while preserving historical drafts. Do not mix user-role management into this page.

**Required skills:** `supabase`, `frontend-design`, `vercel:nextjs`, and `vercel-react-best-practices`.

**Verification:** Test company lifecycle, detection phrases, catalog assignment/removal, shared filters, special/add-on behavior, inactive companies/items, and RBAC.

**Documentation:** Update `MEMORY.md`, `BUSINESS-RULES.md`, `ARCHITECTURE.md`, `API-CONTRACT.md`, `DESIGN-SYSTEM.md`, `TESTING.md`, and the code map when required.

## 9. Company-aware quotation options

read ​docs/START-HERE.md​, then load only the routed documents and implementation files needed for that prompt. Treat every prompt as a complete vertical slice: backend, frontend, database migration, API contract, tests, verification, and necessary documentation updates. Do not make speculative business rules, hard-code rates or fees, expose secrets, persist PDFs locally, or guess uncertain extracted values.

**Objective:** Make insurer detection automatically drive the correct template, mandatory specials, and allowed add-ons during review.

**Required scope:**

- On successful insurer detection, select that company’s active default template automatically and attach its active mandatory specials.
- Allow staff to override only to another active template explicitly eligible for that company. Warn on a mismatch and preserve the chosen template in the reviewed snapshot.
- Show only company-authorized add-ons in review. Render them as accessible plus-style cards with logo, label, and hover/focus details.
- Keep specials automatically selected. Staff may select or deselect only allowed add-ons; company Admin configuration controls what appears.
- Make unavailable/inactive items impossible to select for new drafts while preserving their historical snapshot representation.

**Constraints:** Do not reintroduce a generic package selector that ignores insurer configuration. Do not change historical generated PDFs.

**Required skills:** `vercel:nextjs`, `frontend-design`, and `vercel-react-best-practices`.

**Verification:** Test insurer detection, automatic default selection, controlled override, special inclusion, add-on filtering, inactive behavior, accessibility, and snapshot integrity.

**Documentation:** Update `MEMORY.md`, `BUSINESS-RULES.md`, `API-CONTRACT.md`, `DESIGN-SYSTEM.md`, and `TESTING.md` when applicable.

## 10. Admin users: focused, clear, and notification-aware

read ​docs/START-HERE.md​, then load only the routed documents and implementation files needed for that prompt. Treat every prompt as a complete vertical slice: backend, frontend, database migration, API contract, tests, verification, and necessary documentation updates. Do not make speculative business rules, hard-code rates or fees, expose secrets, persist PDFs locally, or guess uncertain extracted values.

**Objective:** Make the Users area a polished, dedicated employee-management workspace.

**Required scope:**

- Keep this page limited to employee accounts: internal email address, role, status, invitation/resend state, active sessions, session revoke, account activity, and message delivery status.
- Enforce exact `@risklocker.com` validation in every UI and API path.
- Provide contextual help, confirmation for role/status/revocation changes, clear permissions guidance, and readable empty/loading/error states.
- Allow permitted Admin actions to create invitations, resend invitations, change roles, disable/enable accounts, and revoke sessions while generating the required role/account notifications.
- Preserve Manager limits and backend role checks.

**Constraints:** Do not include companies, templates, benefits, storage, or extraction configuration in the Users page. Do not allow shared/group addresses as accounts.

**Required skills:** `frontend-design`, `vercel:nextjs`, and `vercel-react-best-practices`.

**Verification:** Test email validation, role boundaries, invite resend, delivery status, session revocation, disablement, accessibility, and no unauthorized UI/API actions.

**Documentation:** Update `MEMORY.md`, `API-CONTRACT.md`, `DESIGN-SYSTEM.md`, and `TESTING.md` when applicable.

## 11. Admin extraction-data workspace

read ​docs/START-HERE.md​, then load only the routed documents and implementation files needed for that prompt. Treat every prompt as a complete vertical slice: backend, frontend, database migration, API contract, tests, verification, and necessary documentation updates. Do not make speculative business rules, hard-code rates or fees, expose secrets, persist PDFs locally, or guess uncertain extracted values.

**Objective:** Give Admins first-class UI for managing extraction fields and approved reference datasets.

**Required scope:**

- Add dedicated Admin screens for field registry, two-column field datasets, vehicle brands/models, and road-tax imports.
- Provide downloadable templates, drag/drop or file-picker import, preview-before-commit, row-level errors, duplicate handling, activation/deactivation, effective dates, source-reference requirements, import history, and export.
- Keep data entry clear: field variant datasets use exactly two columns; vehicle and road-tax templates use their defined structured columns.
- Replace mutable arbitrary JSON request bodies with Pydantic request/response schemas for these operations.
- Ensure all import and change operations are RBAC-protected and audited.

**Constraints:** No raw database editor, no unreviewed bulk activation, and no silent correction of invalid rate/source data.

**Required skills:** `supabase`, `supabase-postgres-best-practices`, `vercel:nextjs`, and `frontend-design`.

**Verification:** Add API, migration, validation, RBAC, and browser tests for every import workflow and error state.

**Documentation:** Update `MEMORY.md`, `ARCHITECTURE.md`, `API-CONTRACT.md`, `DESIGN-SYSTEM.md`, `TESTING.md`, `OPERATIONS.md`, and the code map when required.

## 12. Template library and precise builder

read ​docs/START-HERE.md​, then load only the routed documents and implementation files needed for that prompt. Treat every prompt as a complete vertical slice: backend, frontend, database migration, API contract, tests, verification, and necessary documentation updates. Do not make speculative business rules, hard-code rates or fees, expose secrets, persist PDFs locally, or guess uncertain extracted values.

**Objective:** Make template management understandable and the existing editor precise enough for production use.

**Required scope:**

- Replace the difficult template listing with searchable, company-filtered management views, clear active/default indicators, safe copy/archive actions, and understandable template ownership.
- Improve drag/drop precision with snapping, alignment guides, keyboard movement, resize handles, layer ordering, selection controls, undo/redo, and smaller visual elements/shapes.
- Add a reusable asset library for custom PNG backgrounds and SVGs, including validation, metadata, preview, placement controls, and renderer compatibility.
- Store user-uploaded reusable assets in approved private Supabase Storage with database metadata and access controls. Do not persist them in application-server or repository directories.
- Keep template rendering deterministic and enforce existing locked-template protections.

**Constraints:** Do not store generated PDFs in the repository or server filesystem. Do not break historical templates or generated PDF snapshots.

**Required skills:** `supabase`, `vercel:nextjs`, `frontend-design`, and `vercel-react-best-practices`.

**Verification:** Test template copy/archive, company filtering, keyboard and pointer editing, snapping/undo/redo, PNG/SVG validation, private asset authorization, and deterministic rendering.

**Documentation:** Update `MEMORY.md`, `ARCHITECTURE.md`, `DESIGN-SYSTEM.md`, `API-CONTRACT.md`, `REFERENCES.md`, `TESTING.md`, and the code map when required.

## 13. History, trash, PDF storage, and operational clarity

read ​docs/START-HERE.md​, then load only the routed documents and implementation files needed for that prompt. Treat every prompt as a complete vertical slice: backend, frontend, database migration, API contract, tests, verification, and necessary documentation updates. Do not make speculative business rules, hard-code rates or fees, expose secrets, persist PDFs locally, or guess uncertain extracted values.

**Objective:** Complete the daily staff workflow after upload and generation without weakening data retention or access controls.

**Required scope:**

- Refine History around quotation job name, owner, insurer, vehicle, status, source/generated timestamps, and direct continuation to Check Values.
- Preserve owner/role visibility rules and the five-recent-job sidebar model.
- Keep private Supabase source/generated PDF storage, retention, deletion, restore, trash expiry, byte-range downloads, and audit behavior correct.
- Make storage and readiness screens report actual configuration state and actionable next steps.
- Keep Microsoft/SharePoint/OneDrive archive optional and backend-only; do not treat an unavailable archive integration as a product failure.

**Constraints:** Never persist source or generated PDFs in the repository or application-server directories. Never expose storage/service-role secrets to the frontend.

**Required skills:** `supabase`, `vercel:nextjs`, and `vercel-react-best-practices`.

**Verification:** Test history search/filter, owner isolation, job continuation, source/generated access, retention/trash transitions, restore/purge, range download, and optional archive status.

**Documentation:** Update `MEMORY.md`, `ARCHITECTURE.md`, `API-CONTRACT.md`, `OPERATIONS.md`, `TESTING.md`, and the code map when required.

## 14. API hardening, automated verification, and release readiness

read ​docs/START-HERE.md​, then load only the routed documents and implementation files needed for that prompt. Treat every prompt as a complete vertical slice: backend, frontend, database migration, API contract, tests, verification, and necessary documentation updates. Do not make speculative business rules, hard-code rates or fees, expose secrets, persist PDFs locally, or guess uncertain extracted values.

**Objective:** Finish the project with enforceable contracts, security controls, automated checks, and release evidence.

**Required scope:**

- Replace remaining mutable `dict` request payloads with typed Pydantic request/response models and clear validation/error conventions.
- Remove dormant configuration flags that are not implemented, and update environment examples/docs accordingly.
- Add application-level rate limiting and security-header policy after documenting the chosen deployment/gateway responsibility; do not claim external controls are active unless configured and verified.
- Add backend HTTP route/RBAC/session/mail-outbox tests, extraction/dataset/road-tax regressions, browser tests from passwordless login through logout and PDF generation, and a GitHub Actions workflow.
- Run all required checks: backend tests, frontend production build, browser tests, code-map generation/check, documentation-link validation, and Mermaid validation.

**Constraints:** Keep Supabase/Postgres as the only application-data store, preserve private Supabase PDF storage, and preserve deterministic reviewed-data PDF generation.

**Required skills:** `supabase`, `vercel:nextjs`, `vercel-react-best-practices`, `agent-browser`, and `web-design-guidelines`.

**Verification:** CI must fail on backend/API/RBAC regressions, frontend build failure, browser workflow failure, or stale generated code map. Confirm the final documentation records limitations as limitations, not completed fixes.

**Documentation:** Update `MEMORY.md` and every canonical document affected by completed behavior; refresh `docs/generated/CODEBASE-MAP.md` after structure, routes, schema, environment, or major behavior changes.
