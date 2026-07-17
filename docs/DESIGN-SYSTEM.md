# Risklocker Design System

## Direction

Build a quiet, work-focused internal dashboard for repeated daily use. Favor scanability, compact controls, predictable navigation, and clear comparison over marketing composition.

## Foundations

- Use Be Vietnam Pro with a system sans-serif fallback.
- Base text is 16 px; supporting text is 14 px; labels are 12-14 px.
- Use semantic `rl-*` tokens from `frontend/src/app/globals.css`; do not introduce one-off component colors.
- Cards and panels use at most an 8 px radius. Do not nest decorative cards.
- Keep fields, buttons, toolbars, and template-canvas controls dimensionally stable.

## Interaction and Accessibility

- Use Lucide icons for familiar commands. Icon-only controls require accessible labels and tooltips.
- Every interactive control needs default, hover, focus-visible, active, disabled, loading, and error behavior.
- Keyboard navigation and visible focus are required. Target WCAG 2.2 AA.
- Use checkboxes/toggles for binary choices, menus for option sets, and numeric controls for numeric values.
- Error messages tell the user what to do next.

## Workflow Screens

- Preserve Upload -> Check Values -> Generate PDF.
- Review uses a sticky action bar, source PDF on the left, and extracted text plus editable fields on the right. Do not expose raw extraction internals.
- The template builder uses a full-screen toolbar, left element library, centered A4 canvas, and right property inspector. Canvas actions must not resize the surrounding layout.
- Admin uses stable sub-navigation for Users, Companies, Templates, Benefits, Storage, and System Checks.
- Long filenames and field values wrap or truncate with a discoverable full value; they must not overlap controls.

## Staff Language

Use `Review / Edit`, `Please check this value.`, `Enhanced reading`, and `PDF Expired`. Use the approved statuses from [BUSINESS-RULES.md](BUSINESS-RULES.md). Do not reveal technical implementation terms to Staff.
