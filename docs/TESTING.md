# Testing

## Test Coverage

| Area | Coverage location |
| --- | --- |
| Configuration and required secure settings | `tests/test_backend_config.py`, `tests/test_config.py` |
| Extraction and deterministic rendering | `tests/test_extraction_pipeline.py`, `tests/test_extraction_regression.py` |
| Upload and PDF hardening | `tests/test_hardening.py` |
| Private PDF storage, byte ranges, and retention | `tests/test_pdf_storage.py` |
| Passwordless policy, code hashing/expiry/throttling, session rolling/expiry/revocation, and browser-storage regression | `tests/test_security.py` |
| Authentication HTTP contract, secure cookie, login/logout, revoked and disabled sessions | `tests/test_auth_http.py` |
| Notifications, invitations, role/status notices, recipient isolation, mark-read, and Admin mail test RBAC | `tests/test_notifications.py` |

## Commands

- Run the full repository check with `npm run test`. It runs backend pytest coverage and the frontend production build.
- Run the code-map validation with `npm run code-map:check`.
- Run the smoke workflow with `./.venv/Scripts/python.exe commands/smoke-test.py` when exercising configured local services.

## Verified Baseline

On 2026-07-17, `npm run test` completed successfully: 90 backend tests passed and the frontend production build succeeded.

## Known Coverage Gaps

- Authentication has focused HTTP route coverage, but non-authentication routes still lack broad HTTP/RBAC integration coverage.
- There are no browser end-to-end tests for login, upload, review, generation, history, trash, or admin flows.
- The repository has no checked-in CI workflow that runs the test and build checks remotely.
- The existing suite is valuable unit/regression coverage, but a passing result does not prove production deployment controls, browser behavior, or full authorization paths.

## Change Expectations

- Use focused tests for the subsystem changed, then run the required build or end-to-end check proportionate to risk.
- Add only anonymized, deterministic fixtures under `tests/fixtures/` for extraction regressions.
- Never depend on private customer PDFs, external process folders, generated PDFs, caches, or runtime secrets in tests.
- Update tests when API behavior, extraction behavior, security validation, rendering behavior, storage behavior, or business rules change.
