# Project Context

## Purpose

Risklocker Quotation Converter is a private internal application for converting insurer motor quotations into reviewed, versioned Risklocker PDFs. It is designed for repeated staff use, not public self-service.

## Staff Journey

1. Upload one or more insurer quotation PDFs.
2. Check extracted Risklocker values against the source document.
3. Select a Risklocker template, package, and applicable benefit cards.
4. Save reviewed values and generate a deterministic PDF.

## Scope

- Motor quotation extraction and review.
- Insurer-aware candidate mapping for Etiqa, AmGen/AmAssurance/Kurnia, QBE/Liberty, STMB, Lonpac, and unknown motor documents.
- Versioned output PDFs, private source-PDF access, history, and trash management.
- Administrative configuration for users, companies, templates, benefits, dictionaries, storage, and system checks.

## Current Boundaries

- The application processes PDFs; backend validation is the authority for accepted upload formats.
- Customer examples and process references are external private development material, not runtime dependencies.
- No paid API is required for the supported workflow.

For mandatory constraints and staff-facing behavior, read [BUSINESS-RULES.md](BUSINESS-RULES.md).
