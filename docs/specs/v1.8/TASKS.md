# CodexBar v1.8 — Tasks

Status: frozen for implementation
Release target: v1.8.0 — Plan
Baseline: v1.7.0 — Diagnose

Implementation rule: complete phases in dependency order. Do not start the next phase with a red gate.

## Global constraints

- Preserve the user's current unstaged root `README.md`.
- Do not mutate unrelated History/Context/reset persistence.
- Do not add a dependency/package solely for Plan.
- Prefer extending existing harness seams.
- Every new behavior test must fail for the intended reason before implementation.
- Existing REQ fixes remain traceable to their historical requirement, not invented v1.8 REQs.

## Phase map

| Phase | Theme | Tasks | Exit |
|---|---|---|---|
| A | spec + coherence baseline | 810..819 | decisions/ADR + existing-contract fixes green |
| B | Plan policy + evaluator | 820..829 | pure canonical vectors + architecture invariants green |
| C | settings schema/configuration | 830..839 | v3 compatibility + GUI/CLI configuration green |
| D | Current Details | 840..849 | PlanPanel/current presenter green |
| E | Plan breach alerts | 850..859 | transition harness + runtime integration green |
| F | regression + physical + release prep | 860..869 | global/physical/docs evidence ready |

Dependencies:

```text
A -> B -> C -> D -> E -> F
```

## Phase A — Spec and coherence baseline

### TASK-810 — Freeze v1.8 spec package

Review/freeze:

- PRODUCT;
- DECISIONS;
- REQUIREMENTS;
- UCs/ACs;
- ARCHITECTURE;
- TEST-MATRIX;
- TRACEABILITY;
- ADR-008.

No code before normative conflicts are resolved.

### TASK-811 — Correct root product-state metadata

Update root product docs to reflect released v1.7 and active v1.8 planning.

Update roadmap conceptual Plan model from duplicate/generic terminology to canonical reserve + checkpoints + fixed Plan breach opt-in.

Do not overwrite local README work.

### TASK-812 — Add ADR-008

Record schema-v3 shape, v1/v2 read compatibility, explicit-save upgrade, exact-key behavior and downgrade consequence.

### TASK-813 — Extract shared neutral quantities compatibly

Create neutral owner for `TimeToReset` and `FractionDelta`.

Preserve historical imports by importing/re-exporting from old modules.

Run focused Context/analytics tests before proceeding.

### TASK-814 — Fix expected redeem refetch failure boundary

Broaden successful-refetch failure handling to `UsageError`.

Add schema/parse failure regression.

Verify all redeem safety tests.

### TASK-815 — Normalize duplicate source window IDs

Add duplicate-duration/source vector and normalize to `UsageSchemaError`.

Verify source/parser/current tests.

### TASK-816 — Baseline gate

Run full gate.

Stop if any released contract regresses.

## Phase B — Plan policy and evaluator

### TASK-820 — Add checkpoint settings-domain model

Implement `UsagePlanCheckpoint` and `UsagePlanCheckpointPolicy`.

Tests:

- unique coordinates;
- non-monotonic accepted;
- canonical order;
- lookup by opaque window ID.

### TASK-821 — Extend AppSettings in memory

Add empty checkpoint policy + false Plan breach default.

Make functional updates preserve every unedited field.

No persistence change yet.

### TASK-822 — Implement pure Plan evaluator

Add application-level Plan resolution/compliance/assessment and `evaluate_window_plan`.

No wall clock, I/O, concurrency or History/Context import.

### TASK-823 — Add canonical Plan vector suite

Implement P01..P14 as parameterized tests.

### TASK-824 — Add v1.8 architecture harness

Protect `INV-PLAN-*`.

### TASK-825 — Phase B gate

Run focused + full gate.

## Phase C — Settings schema/configuration

### TASK-830 — Implement schema v3 encode/decode

Extend existing `JsonSettingsRepository`.

Preserve v1/v2 read behavior and atomic save.

### TASK-831 — Schema-v3 compatibility vectors

Add S01..S08.

Keep existing v1/v2 tests unchanged/green.

### TASK-832 — Extend CLI Settings inspection

Render Plan opt-in/checkpoints and source schema.

Do not add mutation CLI unless separately required.

### TASK-833 — Add typed checkpoint editor to existing Settings UI

Use typed row controls/add-remove behavior.

Do not implement a free-text mini-language.

Preserve absent-window policies.

### TASK-834 — Preserve all AppSettings fields on GUI edits

Refactor candidate construction minimally (e.g. immutable replacement) so new fields cannot be dropped.

### TASK-835 — Settings UI/CLI tests

Extend existing generic tests only where necessary; add Plan-specific UI vectors.

### TASK-836 — Phase C physical check

Open/save/cancel/reset/reopen Settings on target or validated GUI environment.

### TASK-837 — Phase C full gate

## Phase D — Current Details

### TASK-840 — Retain current AppSettings in CurrentAccountPresenter

Update `apply_settings()` to update both Budget and stored settings.

While touching this path, use configured `UsagePolicy` for account usage view state.

### TASK-841 — Add Plan view-state composition

Evaluate CURRENT captured windows without source reread.

Withhold current Plan windows/claim when usage is STALE.

### TASK-842 — Add PlanPanel

Render:

- not configured;
- no active checkpoint;
- reset unavailable/invalid;
- active checkpoint;
- effective floor source;
- signed margin;
- compliance.

Do not move Budget calculation into PlanPanel.

### TASK-843 — Current Details tests

Add semantic rendering/presenter tests.

Protect existing Reset/Budget/Redeem panels.

### TASK-844 — Phase D full gate

## Phase E — Plan breach alerts

### TASK-850 — Implement Plan transition tracker/service

Add CURRENT-only in-memory tracker with policy/cycle baseline semantics.

Use existing `NotificationPort`.

### TASK-851 — Add Plan notification message

Factual wording only.

No prediction/advice/automatic action.

### TASK-852 — Integrate into existing TrayController snapshot path

Process Plan alerts from the same `_state_from_snapshot()` path used by normal refresh and `adopt_snapshot()`.

No second polling loop.

### TASK-853 — Apply Plan settings live

Extend existing Settings apply path to update Plan alert policy/opt-in.

### TASK-854 — Plan alert unit sequences

Implement A01..A10.

### TASK-855 — Extend physical notification harness

Extend `scripts/validate_alerts.py` rather than creating a parallel near-copy.

Keep all old scenario names/behavior valid.

### TASK-856 — Post-redeem adoption regression

Mock redeem/refetch must exercise the same Plan path with no extra source read/mutation.

### TASK-857 — Phase E full gate

## Phase F — Regression, evidence and release prep

### TASK-860 — Full protected baseline

Run all v1.0–v1.7 regression families plus v1.8 tests.

### TASK-861 — Target physical validation

Validate Settings, PlanPanel, notification transitions, native/Qt fallback and window lifecycle.

No real credit consumption required.

### TASK-862 — Traceability closure

Map every REQ/UC/AC/INV to evidence.

Remove orphan/duplicate tests discovered during implementation only when semantic coverage remains explicit.

### TASK-863 — Documentation integration

Update:

- root PRODUCT_SPEC;
- ROADMAP;
- TRACEABILITY/global docs;
- README only by reconciling against the user's already modified local README.

No blind replacement.

### TASK-864 — Version/release preparation

Only after implementation/evidence green:

- bump `pyproject.toml`;
- regenerate lock as required;
- validate `uv run`, editable/install tool modes;
- hosted CI 3.12/3.13/3.14;
- physical target evidence;
- then normal release/tag sequence.

## Deferred maintenance tasks not in v1.8 critical path

Do not mix these into a failing Plan phase:

- unify redeem duplicate enums;
- rename historical `reset_at`;
- rename migration metadata property;
- remove/rework CurrentAccountController only after separate use audit;
- eliminate startup Settings double-read only if a zero-cost integration opportunity emerges;
- clean tracked `.omx` runtime artifacts;
- remove accidental empty `:1:1` files.

The last two are suitable for a separate CHORE commit before/after functional work, but they are not Plan acceptance gates.
