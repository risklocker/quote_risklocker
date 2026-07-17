# Repository Structure

## Top-Level Ownership

| Path | Purpose |
| --- | --- |
| `backend/` | FastAPI application, extraction, services, rendering, and storage adapter |
| `frontend/` | Next.js application, routes, shared UI components, and API client |
| `migrations/` | Ordered Supabase/Postgres schema migrations |
| `tests/` | Backend regression, security, storage, configuration, and extraction coverage |
| `commands/` | Local run, migration, maintenance, smoke-test, and code-map scripts |
| `docs/` | Governed project knowledge base and generated code map |

## Navigation

- Start every repository task at [START-HERE.md](START-HERE.md).
- Use [PROJECT-DIAGRAM.md](PROJECT-DIAGRAM.md) for the complete visual workflow and system overview.
- Use [generated/CODEBASE-MAP.md](generated/CODEBASE-MAP.md) to locate routes, symbols, migrations, tests, and commands.
- Inspect current code before editing; the map is a navigation tool, not a source of truth.
- Runtime template assets are under `backend/app/assets/template_assets/` because both the builder and deterministic renderer need deployed access.

## Documentation Ownership

The canonical document for each topic is listed in [START-HERE.md](START-HERE.md). Do not add parallel plans, duplicate maps, or feature-specific Markdown files when the knowledge belongs in an existing document.
