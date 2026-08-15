# CodexBar v1.8 Specification Package

Theme: **Plan**

Status: **implementation complete; release preparation**

Validated release baseline: `v1.7.0` — Diagnose
Release candidate: `v1.8.0` — Plan
Product-spec baseline commit: `1d9f53150adb1aa6a7fb4573dab023c8bd4f4f7c`
Implementation-complete baseline: `b8b83abe4fae33ed873e33cb1a3c5462366266dd`

v1.8 answers:

> How does Current compare with the explicit operating plan configured by the user?

The normative package is intentionally layered. Read it in this order:

1. `PRODUCT.md`
2. `DECISIONS.md`
3. `COHERENCE-BASELINE.md`
4. `REQUIREMENTS.md`
5. `USE-CASES-AND-ACCEPTANCE.md`
6. `ARCHITECTURE.md`
7. `TEST-MATRIX.md`
8. `TRACEABILITY.md`
9. `TASKS.md`
10. `SPEC-REVIEW.md`
11. `../../adr/ADR-008-settings-schema-v3-plan-policy.md`

Supporting planning/history documents remain useful for provenance:

- `CANDIDATE-SCOPE.md`
- `OPEN-DECISIONS.md`
- `PLANNING.md`
- `ROOT-DOC-UPDATES.md`

## Implementation sequencing

Phase A in `TASKS.md` was a pre-implementation coherence gate, not a fifth functional implementation part.

The four functional macro-parts were completed as:

1. **Core Plan** — policy + pure evaluation (`Phase B`).
2. **Settings + runtime integration** — canonical persistence/configuration and existing-runtime composition (`Phase C` plus presenter integration in `Phase D`).
3. **UI + alerts** — Current Details Plan surface and factual breach notifications (`Phases D–E`, implemented together while preserving the architecture boundary).
4. **Regression + release hardening** — global/physical/docs/release closure (`Phase F`, current).

The implementation baseline, post-bump local gate, version-authority modes and physical Plan/release-candidate smoke are green. Release publication still requires exact-commit hosted CI and annotated-tag closure.

## Root README ownership

The root repository `README.md` contained a pre-existing local Ubuntu/Ayatana/uv-tool expansion. Release preparation preserved that content and reconciled v1.8 Plan documentation onto the reconstructed local version rather than replacing it from HEAD.

The reconciled README is now part of the intended v1.8.0 release-prep diff.
