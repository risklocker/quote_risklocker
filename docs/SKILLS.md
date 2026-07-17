# AI Skill Routing

Load only skills relevant to the current request. Skills guide work but do not override `AGENTS.md`, [BUSINESS-RULES.md](BUSINESS-RULES.md), tests, or user decisions.

## Project-local skills (installed under `.opencode/skills/`)

These skills encode Risklocker's actual codebase conventions. They are registered in `opencode.json` via `skills.paths` and are preferred over generic external skills whenever they apply.

| Skill folder | Use when |
| --- | --- |
| `risklocker-backend` | Editing the FastAPI backend: `backend/app/**`. Covers services pattern, RBAC helpers, `AppError`, `deps.py` auth chain, `get_settings()` env requirements, injected-`sender` mail pattern, route/schemas conventions. |
| `risklocker-frontend` | Editing the Next.js frontend: `frontend/src/**`. Covers App Router layout, `rl-*` design tokens (from `tailwind.config.ts`), `AppShell` nav pattern, `api<T>()` cookie client, WCAG 2.2 AA accessibility, Lucide icons, `StatusBadge` conventions. |
| `risklocker-testing` | Writing or extending tests under `tests/**`. Covers the `FakeSession` variants, `ScalarRows`, `dependency_overrides`, `os.environ.update` at module load, no `conftest.py`, injected `sender` lambda, fixture file rules. |
| `risklocker-verification` | **Mandatory before declaring any task "done" or "verified".** Covers the full verification sequence and the env-check rule (see below). |
| `risklocker-database` | Editing `migrations/**` or `backend/app/models/**`. Covers migration conventions (`BEGIN/COMMIT`, `IF NOT EXISTS`, `RLS` + `REVOKE`, `gen_random_uuid()`), `TimestampMixin`, `StrEnum`-as-string enums, ordered migration filenames. |

### The verification rule (enforced by `risklocker-verification`)

A task is **not** verified until all of the following pass:

1. `.\.venv\Scripts\python.exe -m pytest tests/ -v` — backend tests green.
2. `npx next build` from `frontend/` — frontend production build succeeds.
3. The backend **actually starts** against the real `.env`:
   - `npm run backend` must reach the "Started server process" line without raising.
   - This calls the real `get_settings()`, which reads `.env`. It is the only check that proves the runtime config is complete.
4. `.\.venv\Scripts\python.exe commands/update-code-map.py --check` — the code map is current.

If step 3 fails because `.env` is missing required keys (compare against `.env.example`), the agent must **report it as a blocker before claiming success**. Declaring a task complete while `npm run backend` cannot start is a verification failure, regardless of how many unit tests pass. Unit tests use mocked settings via `dependency_overrides` and `os.environ.update`; they do not exercise the real config loader.

## External skills (fallback)

Use external skills only for capability not covered by a project-local skill above.

| Work | Required or relevant skills |
| --- | --- |
| Supabase platform specifics beyond this repo's conventions | `supabase`, `supabase-postgres-best-practices` |
| Next.js platform specifics beyond this repo's conventions | `vercel:nextjs`, `vercel-react-best-practices` |
| New or substantially reshaped UI patterns | `frontend-design` |
| UI accessibility or UX audit beyond the project rules | `web-design-guidelines` |
| Browser workflow verification | `agent-browser` or `vercel:agent-browser-verify` |
| Broad debugging not scoped to a known subsystem | `vercel:investigation-mode` |
| Long repository work or broad exploration | `codex-token-efficiency` |
| Missing capability | `find-skills` before proposing an install |

Read the selected skill instructions completely before using a skill. Do not load unrelated skills just because they are available.