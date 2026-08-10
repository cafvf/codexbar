# CodexBar v1.6 — Implementation Plan

Status: frozen for implementation

## Strategy

Implement semantics from storage outward:

1. establish 180-day observational substrate;
2. implement pure cycle/reference selection;
3. implement empirical summaries;
4. compose application query;
5. expose Context UI;
6. characterize/harden;
7. validate/release.

This order prevents UI or repository details from deciding statistical semantics.

## Expected code areas

Likely additions:

- `domain/context.py`
- `application/context.py`
- history repository query extension
- `ui/context_panel.py` or equivalent view-model/panel
- v1.6 validation/characterization script(s)

Likely modifications:

- history retention policy;
- composition root;
- Open Details composed panel;
- README/PRODUCT_SPEC/release metadata.

Avoid unless measurement proves necessary:

- history schema migration;
- new Context database;
- settings schema v3;
- notification-policy integration;
- reset-ledger coupling.

## Increment policy

As agreed for current development workflow:

- implement a complete phase;
- run phase gate;
- run Ruff autofix before global gate;
- user runs/validates locally;
- fix all failures;
- one commit/push per completed phase.

All corrective delivery packages should be root-ready ZIP archives.
