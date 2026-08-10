# CodexBar v1.4 — Task Decomposition

Status: implementation complete; release-close hygiene pending  
Baseline: v1.3.0  
Release: v1.4.0 — Understand

## Numbering

v1.4 uses task block `TASK-400..TASK-499`.

This block is release-local planning metadata. Requirement identifiers remain authoritative.

## Phase C1 — Analytical contracts

### TASK-400 — Define historical analytical read models

**Goal:** create application-level immutable contracts for analytical requests/results.

**Covers:**
- AC-ANALYTICS-007..015
- AC-ANALYTICS-016..021
- AC-ANALYTICS-027..033

**Expected outputs:**
- analysis period/request value objects;
- historical summary value object;
- observed-increase representation;
- explicit empty/unavailable result semantics where appropriate.

**Constraints:**
- no Qt;
- no SQLite;
- no provider parsing;
- Decimal/fraction semantics preserved;
- timezone-aware timestamps only.

**Primary evidence:**
- `tests/unit/test_history_analytics.py`

**Depends on:** none.

---

### TASK-401 — Implement pure descriptive analytics

**Goal:** implement deterministic summary and observed-increase calculations over historical samples.

**Covers:**
- AC-ANALYTICS-007..021
- AC-ANALYTICS-027..033

**Required cases:**
- empty;
- singleton;
- constant;
- increasing;
- decreasing;
- mixed sequence;
- multiple observed increases;
- sequence `0.82, 0.63, 0.41, 1.00, 0.91`.

**Must not implement:**
- interpolation;
- forecast;
- ETA;
- token accounting;
- time-in-state;
- sample mean as time average.

**Depends on:** TASK-400.

---

### TASK-402 — Define analytical service/use case

**Goal:** create application orchestration that receives an interval/window identity, reads history through a port,
and returns analytical contracts.

**Covers:**
- AC-ANALYTICS-001..006
- AC-ANALYTICS-034..040

**Expected behavior:**
- one captured end instant per request;
- explicit 24h/7d/30d interval mapping;
- normalized handling of expected history failures;
- no mutation of current state/history.

**Depends on:** TASK-400, TASK-401.

---

## Phase C2 — Read-side history extensions

### TASK-410 — Add efficient historical window discovery

**Goal:** extend the history read boundary so distinct stable `UsageWindowId` values can be discovered without
materializing every historical snapshot solely for identity discovery.

**Covers:**
- AC-ANALYTICS-022..026A
- PERF-GUARD-006

**Expected outputs:**
- application read contract for historical window discovery;
- SQLite schema-v1 implementation;
- deterministic identity ordering policy.

**Constraints:**
- schema remains v1;
- label is attribute, not identity;
- historical-only windows remain discoverable.

**Depends on:** TASK-400.

---

### TASK-411 — Add non-creating read path for absent history

**Goal:** ensure analytical reads against an absent history store do not instantiate `SqliteHistoryRepository`
in a way that creates the database.

**Covers:**
- AC-ANALYTICS-039..040
- AC-HISTORY-UI-006A..006B
- INV-ANALYTICS-009

**Expected behavior:**
- absent store remains absent;
- valid empty store remains distinguishable at application/storage level;
- no implicit repair/migration/reset.

**Depends on:** TASK-402.

---

### TASK-412 — Harden analytical history failure mapping

**Goal:** ensure all expected v1.3 history failure classes, including schema failures, are normalized into the
analytical unavailable contract.

**Covers:**
- AC-ANALYTICS-034..038
- AC-HISTORY-UI-033..037

**Required cases:**
- `HistoryReadError`;
- `HistoryCorruptionError`;
- `HistorySchemaError`;
- absent history;
- valid empty history.

**Depends on:** TASK-402, TASK-411.

---

### TASK-413 — Add read-side adapter tests

**Goal:** validate the new schema-v1 analytical queries and absent-store semantics.

**Primary evidence:**
- `tests/unit/test_history_sqlite_analytics_queries.py`

**Covers:**
- AC-ANALYTICS-001..006
- AC-ANALYTICS-022..026A
- AC-ANALYTICS-034
- AC-ANALYTICS-039..040
- PERF-GUARD-006

**Depends on:** TASK-410, TASK-411, TASK-412.

---

## Phase C3 — Analytics acceptance and architecture

### TASK-420 — Add REQ-ANALYTICS-001 acceptance suite

**Goal:** prove the complete user/application behavior of `REQ-ANALYTICS-001`.

**Primary evidence:**
- `tests/acceptance/test_req_analytics_001.py`

**Required scenarios:**
1. half-open interval boundaries;
2. deterministic mixed-sequence summary;
3. singleton;
4. empty;
5. label changes with stable id;
6. equal labels with different ids;
7. historical-only window;
8. forbidden inference outputs absent;
9. read/corruption failure;
10. unsupported schema;
11. absent store remains absent;
12. efficient distinct-window discovery contract.

**Depends on:** TASK-401, TASK-413.

---

### TASK-421 — Add v1.4 analytics architecture guards

**Goal:** protect dependency direction and read-only semantics.

**Primary evidence:**
- `tests/acceptance/test_v1_4_architecture_invariants.py`

**Covers:**
- INV-ANALYTICS-001..009
- retention of v1.3 history architecture invariants.

**Important:** existing protection that current `TrayController` does not directly depend on history storage
must not be weakened.

**Depends on:** TASK-402, TASK-410, TASK-411.

---

### TASK-422 — Phase C analytics gate

**Goal:** run the repository-wide quality gate before any historical GUI implementation.

**Checks:**
- pytest;
- Ruff;
- strict mypy;
- compileall;
- v1.0-v1.3 regression suite;
- no orphan analytics ACs.

**Exit criterion:** `REQ-ANALYTICS-001` implementation-ready/closed at automated level.

**Depends on:** TASK-420, TASK-421.

---

## Phase C4 — Historical presentation model

### TASK-430 — Define history presentation state

**Goal:** map analytical contracts to immutable UI-facing state without performing analytical calculations.

**Covers:**
- AC-HISTORY-UI-016..020
- AC-HISTORY-UI-029..034

**Expected states:**
- loading;
- ready;
- empty;
- unavailable;
- unsupported.

**Expected presentation data:**
- selected period;
- selected stable window id;
- display label;
- summary values;
- observed series;
- localized timestamp-ready fields.

**Depends on:** TASK-422.

---

### TASK-431 — Define historical chart data contract

**Goal:** define discrete observation points consumed by rendering.

**Covers:**
- AC-HISTORY-UI-021..028

**Constraints:**
- every point corresponds to a persisted observation;
- no synthetic forecast/interpolation point;
- observed increases preserved;
- rendering optimization cannot alter summaries.

**Depends on:** TASK-430.

---

### TASK-432 — Add history presentation-model unit tests

**Primary evidence:**
- `tests/unit/test_history_view_model.py`

**Covers:**
- summary formatting;
- localized timestamps;
- positive/negative/undefined observed change;
- empty;
- unavailable;
- unsupported;
- window identity;
- period selection;
- chart point fidelity.

**Depends on:** TASK-430, TASK-431.

---

## Phase C5 — Historical asynchronous controller

### TASK-440 — Implement dedicated HistoryController

**Goal:** orchestrate historical requests independently from current `TrayController`.

**Covers:**
- AC-HISTORY-UI-038..042
- INV-HISTORY-UI-005
- INV-HISTORY-UI-007

**Required behavior:**
- history queries off GUI thread;
- immutable completion state;
- current refresh remains independent.

**Depends on:** TASK-430, TASK-422.

---

### TASK-441 — Add request-generation/stale-completion guard

**Goal:** prevent an older historical request from overwriting a newer user selection.

**Covers:**
- AC-HISTORY-UI-039

**Canonical scenario:**
- request A: 30d/weekly;
- request B: 24h/weekly;
- B completes first;
- A completes later;
- active state remains B.

**Depends on:** TASK-440.

---

### TASK-442 — Handle controller close/cancellation lifecycle

**Goal:** closing history while a worker request is outstanding must not crash or mutate destroyed UI state.

**Covers:**
- AC-HISTORY-UI-040

**Depends on:** TASK-440.

---

## Phase C6 — Historical GUI

### TASK-450 — Build historical view shell

**Goal:** create desktop-accessible historical view.

**Covers:**
- AC-HISTORY-UI-001..006B

**Required behavior:**
- accessible from normal desktop interface;
- default 24h;
- selects a historical window when available;
- absent/empty handled without mutation.

**Depends on:** TASK-440, TASK-432.

---

### TASK-451 — Implement period selection and stable internal window focus

**Covers:**
- AC-HISTORY-UI-007..015

**Required controls:**
- 24h;
- 7d;
- 30d.

**As-built refinement:** stable window identity is internal in v1.4. Current-card navigation preserves an
explicit `UsageWindowId`; global History resolves a deterministic analyzable identity. Arbitrary historical
window browsing is deferred beyond v1.4.

**Depends on:** TASK-450, TASK-441.

---

### TASK-452 — Implement historical summary panel

**Covers:**
- AC-HISTORY-UI-016..020

**Required values:**
- observation count;
- first/latest observation;
- first/latest remaining;
- observed min/max;
- observed change.

**Depends on:** TASK-450.

---

### TASK-453 — Implement historical observation chart

**Covers:**
- AC-HISTORY-UI-021..032
- PERF-GUARD-004..005

**Constraints:**
- discrete observation semantics;
- no inferred reset label from positive change alone;
- no forecast;
- no smoothing that removes observed discontinuities.

**Chart technology decision:**
Use existing Qt capabilities if adequate. If implementation requires a substantial new chart framework,
reassess whether an ADR is warranted before adoption.

**Depends on:** TASK-431, TASK-450.

---

### TASK-454 — Integrate historical unavailable states

**Covers:**
- AC-HISTORY-UI-033..037

**States:**
- corrupt/unreadable;
- unsupported schema;
- empty/absent.

**Depends on:** TASK-450, TASK-412.

---

### TASK-455 — Add REQ-HISTORY-UI-001 acceptance suite

**Primary evidence:**
- `tests/acceptance/test_req_history_ui_001.py`

**Required scenarios:** all scenarios enumerated in the requirement.

**Depends on:** TASK-451, TASK-452, TASK-453, TASK-454.

---

### TASK-456 — Phase C target validation

**Goal:** physically validate Historical Insight on Ubuntu/GNOME/Wayland.

**Validate:**
- real retained data;
- 24h/7d/30d;
- stable focused-window identity through current-to-history navigation;
- responsiveness;
- current refresh while history open;
- absent/empty/error states where reproducible;
- chart readability and discrete semantics.

**Exit criterion:** Phase C closed. Phase A may begin.

**Depends on:** TASK-455 and repository-wide quality gate.

---

## Phase A1 — Current presentation contract

### TASK-460 — Preserve stable UsageWindowId in current view state

**Goal:** extend current presentation state to retain stable window identity.

**Covers:**
- AC-UI-040A
- AC-UI-051..054A
- INV-UI-003-007

**Constraint:** no label matching for navigation.

**Depends on:** TASK-456.

---

### TASK-461 — Preserve whole-percent current presentation semantics

**Goal:** make textual and visual current quota representation consistent with existing whole-percent behavior.

**Covers:**
- AC-UI-036..037
- INV-UI-003-008

**Required regression case:**
- domain remaining = 63.9%;
- existing presentation percentage remains 63%;
- visual indicator matches the presentation percentage.

**Depends on:** TASK-460.

---

### TASK-462 — Add current presentation contract tests

**Goal:** update/add deterministic tests for stable identity, percentage semantics, reset presentation inputs,
state classification and freshness.

**Depends on:** TASK-460, TASK-461.

---

## Phase A2 — Rich current UI

### TASK-470 — Build richer current-window cards

**Covers:**
- AC-UI-034..040A

**Display:**
- label;
- whole percentage;
- visual remaining indicator;
- AVAILABLE/LOW/EXHAUSTED;
- reset information when available.

**Depends on:** TASK-462.

---

### TASK-471 — Add explicit freshness and observation-age presentation

**Covers:**
- AC-UI-041..045

**Depends on:** TASK-470.

---

### TASK-472 — Add reset absolute/relative presentation

**Covers:**
- AC-UI-046..050

**Requirement:** one captured presentation instant is used for relative reset calculations.

**Depends on:** TASK-470.

---

### TASK-473 — Add current-window to historical-window navigation

**Covers:**
- AC-UI-051..054A

**Requirement:** pass stable `UsageWindowId` directly into historical selection.

**Depends on:** TASK-460, TASK-451, TASK-470.

---

### TASK-474 — Preserve tray/Ayatana compatibility

**Covers:**
- AC-UI-055..059
- INV-UI-003-004..005

**Must preserve:**
- canonical glance;
- native helper presentation-only boundary;
- Qt fallback;
- asynchronous/non-overlapping refresh.

**Depends on:** TASK-470, TASK-471, TASK-472, TASK-473.

---

### TASK-475 — Add REQ-UI-003 acceptance suite

**Primary evidence:**
- `tests/acceptance/test_req_ui_003_current_details.py`

**Depends on:** TASK-474.

---

## Phase A3 — Release integration

### TASK-480 — Complete v1.4 architecture/regression gate

**Goal:** run all v1.4 invariants together with all v1.0-v1.3 regression guards.

**Depends on:** TASK-475.

---

### TASK-481 — Complete v1.4 target workstation validation

**Validate physically:**
- richer current state;
- CURRENT vs STALE;
- reset presentation;
- current-to-history navigation;
- historical view;
- Ayatana;
- Qt fallback;
- responsiveness.

**Depends on:** TASK-480.

---

### TASK-482 — Create v1.4 traceability records

**Expected outputs:**
- `docs/TRACEABILITY-REQ-ANALYTICS-001.md`
- `docs/TRACEABILITY-REQ-HISTORY-UI-001.md`
- `docs/TRACEABILITY-REQ-UI-003.md`

Each AC maps to primary test evidence and implementation.

**Depends on:** TASK-480.

---

### TASK-483 — Create v1.4 validation records

**Expected outputs:**
- validation record(s) for automated and target-system evidence.

**Depends on:** TASK-481.

---

### TASK-484 — Update product/release documentation

**Expected updates:**
- `PRODUCT_SPEC.md`;
- `README.md`;
- `CHANGELOG.md`;
- documentation map;
- version references where release-close appropriate.

**Depends on:** TASK-482, TASK-483.

---

### TASK-485 — Final release gate and metadata bump

**Checks:**
- no orphan REQ/UC/AC;
- all task/traceability links resolved;
- pytest;
- Ruff;
- strict mypy;
- compileall;
- release metadata consistency;
- `git diff --check`;
- clean reviewed worktree.

**Depends on:** TASK-484.

---

## Critical path

`400 -> 401 -> 402 -> 410/411/412 -> 413 -> 420/421 -> 422`
`-> 430/431 -> 432 -> 440 -> 441/442 -> 450 -> 451/452/453/454 -> 455 -> 456`
`-> 460 -> 461/462 -> 470 -> 471/472/473 -> 474 -> 475 -> 480 -> 481/482 -> 483 -> 484 -> 485`

## Parallelizable work

After `TASK-402`:
- `TASK-410`, `TASK-411`, and `TASK-412` can proceed largely independently.

After `TASK-430`:
- `TASK-431` and parts of `TASK-440` can proceed in parallel.

After `TASK-470`:
- freshness (`471`), reset presentation (`472`), and navigation (`473`) can proceed in parallel, subject to
  their listed dependencies.

## Recommended implementation increments

### Increment 1 — Analytical core
`TASK-400..422`

Deliverable: headless historical analytics, fully tested.

### Increment 2 — Historical UX
`TASK-430..456`

Deliverable: complete Phase C Historical Insight.

### Increment 3 — Current UX
`TASK-460..475`

Deliverable: complete Phase A richer current state.

### Increment 4 — Release close
`TASK-480..485`

Deliverable: traceable, validated v1.4 release candidate.


### TASK-481A — GUI composition and lifecycle stabilization

- Update v1.4 specifications for Period-only History and explicit missing-reset presentation.
- Inject the current details panel into `TrayShell`; remove post-construction replacement.
- Render CURRENT only on state transitions while retaining backend health supervision on every poll.
- Keep observation-age updates local to `RichUsagePanel`.
- Make History a top-level sibling and stop its poll timer while hidden.
- Preserve explicit `UsageWindowId` on empty historical periods.
- Cancel superseded queued history requests when possible.
- Add lifecycle/integration acceptance tests and repeat TASK-481 target validation.

## Completion registry — v1.4.0 release candidate

- `TASK-400..422`: **COMPLETE** — analytical contracts, read-side extensions, acceptance and architecture.
- `TASK-430..456`: **COMPLETE** — historical presentation/controller/UI and target Phase C validation.
- `TASK-460..475`: **COMPLETE** — richer CURRENT presentation and CURRENT -> History navigation.
- `TASK-480`: **COMPLETE** — architecture/regression gate.
- `TASK-481`: **COMPLETE** after `TASK-481A` lifecycle stabilization and repeated target validation.
- `TASK-481A`: **COMPLETE** — GUI composition/lifecycle stabilization.
- `TASK-482`: **COMPLETE** — v1.4 traceability records prepared.
- `TASK-483`: **COMPLETE** — final target validation record archived.
- `TASK-484`: **COMPLETE** — README/Product Spec/CHANGELOG/release documentation prepared.
- `TASK-485`: **READY FOR FINAL LOCAL GATE** — metadata is prepared for 1.4.0; `uv lock`, repository-wide
  gates, `git diff --check`, staged-diff review, clean worktree, commit and annotated tag remain local
  release-hygiene actions.
