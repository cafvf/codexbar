# Phase H — Validation + Release

Tasks: TASK-780..789

## Goal

Close traceability, target performance, physical validation and v1.7.0 release.

## Tasks

- TASK-780: build generic/final v1.7 validation command/script.
- TASK-781: run real Doctor text/JSON read-only validation.
- TASK-782: validate real History/Context/System Health state.
- TASK-783: run final performance characterization and compare Phase A baseline.
- TASK-784: physical single-instance/Open Details/System Health lifecycle.
- TASK-785: physical Context responsiveness and native/Qt fallback.
- TASK-786: physical redeem responsiveness when safe or capability SKIP.
- TASK-787: finalize README/PRODUCT_SPEC/CHANGELOG/TRACEABILITY/VALIDATION.
- TASK-788: bump release metadata to 1.7.0, regenerate lock, verify single authority.
- TASK-789: final global + hosted CI + physical gate, release commit/tag preparation.

## Gate H

All automated P0 gates green; hosted Python matrix green; performance evidence
recorded; physical validation green or explicitly justified capability SKIP;
release documents closed; v1.7.0 ready for final commit/tag.
