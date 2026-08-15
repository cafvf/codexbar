# CodexBar v1.8 — Tasks

Status: complete; released as v1.8.0
Release: v1.8.0 — Plan
Baseline: v1.7.0 — Diagnose
Implementation-complete commit: `b8b83abe4fae33ed873e33cb1a3c5462366266dd`
Release-prep commit: `dd87b4716fe29c5d433704079b729338c42e33c4`
Release/tag-target commit: `8edf0154f80862c283ea20f5f2e9e5fcbca8e734`

Implementation rule: complete phases in dependency order. Do not start the next phase with a red gate.

## Global constraints

- Preserve the user's current unstaged root `README.md`.
- Do not mutate unrelated History/Context/reset persistence.
- Do not add a dependency/package solely for Plan.
- Prefer extending existing harness seams.
- Every new behavior test must fail for the intended reason before implementation.
- Existing REQ fixes remain traceable to their historical requirement, not invented v1.8 REQs.

## Phase map

| Phase | Theme | Tasks | State | Exit |
|---|---|---|---|---|
| A | spec + coherence baseline | 810..819 | Complete | decisions/ADR + existing-contract fixes green |
| B | Plan policy + evaluator | 820..829 | Complete | pure canonical vectors + architecture invariants green |
| C | settings schema/configuration | 830..839 | Complete | v3 compatibility + GUI/CLI configuration green |
| D | Current Details | 840..849 | Complete | PlanPanel/current presenter green |
| E | Plan breach alerts | 850..859 | Complete | transition harness + runtime integration green |
| F | regression + physical + release prep | 860..869 | Complete | global/physical/docs/hosted/tag closure complete |

Dependencies:

```text
A -> B -> C -> D -> E -> F
```

Implementation commits:

- Phase A: `bfb4933` — coherence baseline;
- Phase B: `9e18915` — Plan policy and evaluator;
- Phase C: `5a1a285` — Settings schema v3 and editor;
- Phases D+E: `b8b83ab` — Plan runtime, UI and alerts;
- release preparation: `dd87b47`;
- evidence closure/tag target: `8edf015`.

## Phase A — Spec and coherence baseline

### TASK-810 — Freeze v1.8 spec package

Review/freeze PRODUCT, DECISIONS, REQUIREMENTS, UCs/ACs, ARCHITECTURE, TEST-MATRIX, TRACEABILITY and ADR-008.

Status: complete.

### TASK-811 — Correct root product-state metadata

Update root product docs to reflect released v1.7 and active v1.8 planning. Update roadmap conceptual Plan model from duplicate/generic terminology to canonical reserve + checkpoints + fixed Plan breach opt-in. Do not overwrite local README work.

Status: complete.

### TASK-812 — Add ADR-008

Record schema-v3 shape, v1/v2 read compatibility, explicit-save upgrade, exact-key behavior and downgrade consequence.

Status: complete.

### TASK-813 — Extract shared neutral quantities compatibly

Create neutral owner for `TimeToReset` and `FractionDelta`. Preserve historical imports by importing/re-exporting from old modules.

Status: complete.

### TASK-814 — Fix expected redeem refetch failure boundary

Broaden successful-refetch failure handling to `UsageError`. Add schema/parse failure regression.

Status: complete.

### TASK-815 — Normalize duplicate source window IDs

Add duplicate-duration/source vector and normalize to `UsageSchemaError`.

Status: complete.

### TASK-816 — Baseline gate

Run full gate.

Status: complete.

## Phase B — Plan policy and evaluator

### TASK-820 — Add checkpoint settings-domain model

Implement `UsagePlanCheckpoint` and `UsagePlanCheckpointPolicy` with unique coordinates, non-monotonic support, canonical order and opaque-ID lookup.

Status: complete.

### TASK-821 — Extend AppSettings in memory

Add empty checkpoint policy + false Plan breach default. Functional updates preserve every unedited field.

Status: complete.

### TASK-822 — Implement pure Plan evaluator

Add application-level Plan resolution/compliance/assessment and `evaluate_window_plan` with no wall clock, I/O, concurrency or History/Context import.

Status: complete.

### TASK-823 — Add canonical Plan vector suite

Implement P01..P14.

Status: complete.

### TASK-824 — Add v1.8 architecture harness

Protect `INV-PLAN-*`.

Status: complete.

### TASK-825 — Phase B gate

Status: complete.

## Phase C — Settings schema/configuration

### TASK-830 — Implement schema v3 encode/decode

Extend existing `JsonSettingsRepository` while preserving v1/v2 read behavior and atomic save.

Status: complete.

### TASK-831 — Schema-v3 compatibility vectors

Add S01..S08 while keeping existing v1/v2 tests green.

Status: complete.

### TASK-832 — Extend CLI Settings inspection

Render Plan opt-in/checkpoints and source schema.

Status: complete.

### TASK-833 — Add typed checkpoint editor to existing Settings UI

Use typed row controls/add-remove behavior; preserve absent-window policies.

Status: complete.

### TASK-834 — Preserve all AppSettings fields on GUI edits

Refactor candidate construction minimally so new fields cannot be dropped.

Status: complete.

### TASK-835 — Settings UI/CLI tests

Status: complete.

### TASK-836 — Phase C physical check

Open/save/cancel/reset/reopen Settings on target or validated GUI environment.

Status: complete on target Ubuntu/GNOME/Wayland.

### TASK-837 — Phase C full gate

Status: complete.

## Phase D — Current Details

### TASK-840 — Retain current AppSettings in CurrentAccountPresenter

Update `apply_settings()` to update both Budget and stored settings; use configured `UsagePolicy` for account usage view state.

Status: complete.

### TASK-841 — Add Plan view-state composition

Evaluate CURRENT captured windows without source reread. Withhold current Plan windows/claim when usage is STALE.

Status: complete.

### TASK-842 — Add PlanPanel

Render not configured, no active checkpoint, reset unavailable/invalid, active checkpoint, effective floor source, signed margin and compliance without moving Budget calculation into PlanPanel.

Status: complete.

### TASK-843 — Current Details tests

Status: complete.

### TASK-844 — Phase D full gate

Status: complete as part of the combined D+E gate.

## Phase E — Plan breach alerts

### TASK-850 — Implement Plan transition tracker/service

Add CURRENT-only in-memory tracker with policy/cycle baseline semantics using existing `NotificationPort`.

Status: complete.

### TASK-851 — Add Plan notification message

Factual wording only; no prediction/advice/automatic action.

Status: complete.

### TASK-852 — Integrate into existing TrayController snapshot path

Process Plan alerts from the same `_state_from_snapshot()` path used by normal refresh and `adopt_snapshot()` with no second polling loop.

Status: complete.

### TASK-853 — Apply Plan settings live

Extend existing Settings apply path to update Plan alert policy/opt-in.

Status: complete.

### TASK-854 — Plan alert unit sequences

Implement A01..A10.

Status: complete.

### TASK-855 — Extend physical notification harness

Extend `scripts/validate_alerts.py` while keeping old scenario behavior valid.

Status: complete and physically validated.

### TASK-856 — Post-redeem adoption regression

Mock redeem/refetch exercises the same Plan path with no extra source read/mutation.

Status: complete.

### TASK-857 — Phase E full gate

Status: complete; combined D+E implementation baseline passed 815 tests plus Ruff/mypy/compileall/diff check.

## Phase F — Regression, evidence and release prep

### TASK-860 — Full protected baseline

Run all v1.0–v1.7 regression families plus v1.8 tests.

Status: complete. Implementation baseline 815 tests; final post-bump release-prep gate 819 tests, Ruff, mypy, compileall and diff check all green.

### TASK-861 — Target physical validation

Validate Settings, PlanPanel, notification transitions, native/Qt fallback and window lifecycle. No real credit consumption required.

Status: complete. Plan-specific validation plus final release-prep native/window lifecycle smoke passed on Ubuntu/GNOME/Wayland.

### TASK-862 — Traceability closure

Map every REQ/UC/AC/INV to evidence.

Status: complete. `docs/specs/v1.8/TRACEABILITY.md` and `docs/TRACEABILITY-v1.8.md` close the implementation and release evidence.

### TASK-863 — Documentation integration

Update PRODUCT_SPEC, ROADMAP, TRACEABILITY/global docs and README only by reconciling against the user's already modified local README.

Status: complete. The pre-existing expanded README was preserved, reconciled with v1.8 Plan documentation, and shipped in the v1.8 release lineage.

### TASK-864 — Version/release preparation

Bump `pyproject.toml`, regenerate lock, validate uv-run/editable/tool modes, hosted CI 3.12/3.13/3.14, physical target evidence, then normal release/tag sequence.

Status: complete.

Release closure evidence:

- project/lock version: 1.8.0;
- final local gate: 819 tests plus Ruff/mypy/compileall/diff check;
- uv-run/editable/uv-tool version modes: green;
- release-prep CI run `31858424480`: SUCCESS;
- tag-target CI run `31858617233`: SUCCESS;
- annotated tag `v1.8.0` remotely verified;
- tag target: `8edf0154f80862c283ea20f5f2e9e5fcbca8e734`;
- remote tag object: `47411ee438fdb10745a5bd1fdce1d76067ab4cee`.

## Deferred maintenance tasks not in v1.8 critical path

These remain separate from the closed v1.8 release:

- unify redeem duplicate enums;
- rename historical `reset_at`;
- rename migration metadata property;
- remove/rework CurrentAccountController only after separate use audit;
- eliminate startup Settings double-read only if a zero-cost integration opportunity emerges;
- clean tracked `.omx` runtime artifacts;
- remove accidental empty `:1:1` files.

The last two remain suitable for a separate CHORE commit and were not Plan acceptance gates.
