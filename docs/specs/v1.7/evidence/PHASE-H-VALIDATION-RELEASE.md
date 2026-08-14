# CodexBar v1.7 Phase H — Validation + Release Evidence

Status: **H1 validation harness prepared; target evidence pending**
Tasks: TASK-780..789
Remote Phase G anchor:
`64d370b303c4be6a8497cc66f9034810cc572db5`

## Delivery split

Phase H is intentionally executed in two release-safe tranches.

### H1 — validation and evidence

H1 adds:

- `scripts/validate_v17_phase_h.py`;
- `scripts/characterize_v17_phase_h.py`;
- a physical target checklist;
- architecture guards for the validation harness.

H1 does **not** bump release metadata and does **not** rewrite release documents
with unobserved evidence.

### H2 — release closure

H2 is authorized only after H1 automated, performance and physical evidence is
reviewed.

H2 will:

- close README / PRODUCT_SPEC / CHANGELOG / TRACEABILITY / VALIDATION;
- set the single `pyproject.toml` version authority to `1.7.0`;
- regenerate `uv.lock`;
- rerun version-mode validation;
- run the final local and hosted gates;
- prepare the release commit and `v1.7.0` tag.

## TASK-780 — final validation harness

`scripts/validate_v17_phase_h.py` runs the real target commands for:

- Doctor text;
- Doctor JSON;
- History inspection;
- reset-ledger inspection;
- desktop integration status;
- all three version execution modes.

The script snapshots CodexBar files under the effective XDG config/data/state
roots before and after Doctor text/JSON execution and requires exact equality.

The script never invokes settings reset, History clear, redeem or any other
destructive operation.

## TASK-781 — real Doctor read-only validation

Pending target run.

Required evidence:

- Doctor text exit 0;
- Doctor JSON exit 0;
- `diagnostics_schema_version = 1`;
- no raw email/token-like diagnostic material;
- persistent-state before/after equality.

## TASK-782 — real History / Context / System Health state

History inspection is captured by the H1 automated harness.

Context and System Health are target GUI surfaces and remain part of the physical
checklist; their factual state must be recorded rather than inferred from hosted
CI.

## TASK-783 — final performance characterization

`scripts/characterize_v17_phase_h.py` reruns the existing Phase A, C and D
characterizers with at least 20 samples and aggregates:

- Phase A app-server / Current / Doctor / History / pre-cache Context metrics;
- Phase C lean candidate read / cold Context / cache-hit metrics;
- Phase D synchronous Qt Context work / background completion;
- optional Phase B SHOW_DETAILS IPC when a live GUI owner is running.

The report includes the frozen Phase A p95 baseline values from
`PHASE-A-BASELINE-DIAGNOSTICS.md` and calculates final deltas/ratios.

Frozen budgets:

- Context cache-hit p95 <= 5 ms;
- Qt Context synchronous p95 <= 50 ms;
- SHOW_DETAILS IPC p95 <= 250 ms;
- local-only Doctor p95 <= 500 ms;
- cold Context p95 <= 150 ms is an engineering target and does not block release
  by itself when the protected hard gates pass and the miss is documented.

## TASK-784..786 — physical validation

See `PHASE-H-PHYSICAL-CHECKLIST.md`.

No script may claim physical shell rendering from an API-only diagnostic.

Redeem is executed only if a safe unresolved capability exists. Otherwise the
physical redeem mutation is an explicit capability SKIP and the already validated
fake/delayed async regression remains required.

## TASK-787..789 — pending H2

Documentation closure, version bump, lock regeneration, final hosted CI and tag
preparation remain pending until H1 evidence is reviewed.

The user-local README working-tree change is intentionally not touched by H1.

## H2 — release preparation

H1 is closed with TASK-780..786 green.

Release preparation performs TASK-787 and TASK-788 by:

- finalizing release-facing README/PRODUCT_SPEC/CHANGELOG/traceability/validation;
- setting the single `pyproject.toml` authority to `1.7.0`;
- regenerating `uv.lock`;
- requiring all three execution modes to report `1.7.0`.

TASK-789 remains open until the post-bump local gate and hosted release-prep CI are
green. The annotated `v1.7.0` tag is created only after that remote closure.

## H2 local closure

TASK-787 — documentation closure: **GREEN**.

TASK-788 — release metadata / lock / single authority: **GREEN**.

Evidence:

- `pyproject.toml` is `1.7.0`;
- `uv.lock` contains CodexBar `1.7.0`;
- runtime version derives from package metadata;
- `uv-run`, editable and isolated `uv-tool` modes all report metadata/runtime
  `1.7.0`;
- post-bump pytest/Ruff/strict-mypy/compileall/diff-check gate is green.

TASK-789 remains pending until the release-prep commit is pushed and hosted CI is
green on that exact commit. Tag creation remains prohibited before that closure.
