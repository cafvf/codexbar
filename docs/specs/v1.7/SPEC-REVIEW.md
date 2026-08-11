# CodexBar v1.7 — Specification Review Checklist

Status: frozen package

## Product

- [x] Diagnose theme has a user-visible capability.
- [x] No forecasting/automatic redeem scope leak.
- [x] v1.8 exploration boundary remains clear.

## Architecture

- [x] diagnostic domain independent of Qt/SQLite;
- [x] one-instance ownership resolved before GuiRuntime;
- [x] Context revisions/cache defined;
- [x] Context async pattern defined;
- [x] redeem process manager preserved;
- [x] account lineage limitation explicit;
- [x] source multi-bucket compatibility defined.

## Evidence gates

- [x] persistent app-server default=no change;
- [x] prune default=no change;
- [x] WAL default=no change;
- [x] Ayatana migration default=no change.

## Verification

- [x] requirements map to acceptance criteria/tests;
- [x] canonical vectors exist;
- [x] Python CI range matches project metadata;
- [x] target performance budgets distinguish computation from UI blocking;
- [x] physical target gates retained.

Implementation may begin with Phase A after this documentation package is applied,
reviewed with `git diff --check`, committed and pushed.
