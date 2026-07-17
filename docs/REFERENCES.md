# References and Assets

## Runtime Template Assets

Runtime template images live in `backend/app/assets/template_assets/` because the template builder and deterministic renderer need them in deployed code.

- The catalog accepts PNG, JPG, JPEG, and SVG files.
- Keep only accepted runtime formats in this deployed directory. Unsupported authoring files belong in the private reference archive, not alongside runtime assets.
- Assets can represent logos, payment/all-driver boxes, backgrounds, insurer marks, icons, and bilingual benefit cards.
- The locked default template is database configuration, not a customer PDF. Admins copy it before editing.
- The unused `clcik for cover.wdp` and `E-hailing.wdp` files were removed on 2026-07-14 because the asset service intentionally ignores `.wdp` files.

## Private Development References

Customer and process examples are outside this repository at:

`C:\Users\user\Desktop\dev\quote\risklocker-reference-archive\process`

Additional former sample uploads are at:

`C:\Users\user\Desktop\dev\quote\risklocker-reference-archive\samples`

These are private development references only. Runtime code and automated tests must never depend on them. Add only anonymized, deterministic regression fixtures under `tests/fixtures/`.
