# Risklocker AI Entry Point

Read `docs/START-HERE.md` before repository work. It routes each request to the smallest relevant project context, code map, and skill guidance.

Non-negotiable rules:

- Use Supabase/Postgres only for application data.
- Use private Supabase Storage for persistent PDFs; never persist PDFs in this repository or application-server directories.
- Keep SharePoint/OneDrive archive optional and backend-only.
- Never expose service-role keys or backend secrets to the frontend.
- Never silently guess uncertain extracted values.
- Generate final PDFs deterministically from reviewed draft data and saved templates, never from AI-generated layout.
- Do not hardcode fees or business formulas.
- Preserve the staff workflow: Upload -> Check Values -> Generate PDF.
- Update the code map when structure, routes, schema, environment variables, or major behavior changes.
