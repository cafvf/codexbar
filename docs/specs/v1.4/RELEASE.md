# CodexBar v1.4 Release Specification

Status: validated release candidate — final repository/tag hygiene pending
Release target: v1.4.0  
Baseline: v1.3.0  
Change taxonomy: EVOLUTION  
Theme: Understand

## Release-close evidence — 2026-08-10

The v1.4 target validation completed with **PASS** on Ubuntu/GNOME/Wayland after GUI lifecycle stabilization.

Validated automated gate:
- pytest: **353 passed**;
- Ruff: **PASS**;
- strict mypy: **PASS** across 37 source files;
- compileall: **PASS**;
- history inspection: schema **1**, `ready_non_empty`;
- native indicator diagnostic API path: **PASS**.

Validated physical behaviors:
- richer CURRENT details and classification;
- CURRENT/STALE distinction and observation age;
- reset presentation;
- CURRENT -> History identity preservation;
- CURRENT refresh with History hidden and visible;
- History 24h/7d/30d with explicit time axis and discrete observations;
- native Ayatana menu/label path.

Qt fallback remained a conditional target check and was not physically re-run in the final v1.4 validation;
its automated/regression contract remains part of the release gate.

The release introduces no history schema migration, no settings schema migration, and no change to v1.3
CURRENT-only historical capture semantics.


## Goal

Turn the bounded observation history introduced in v1.3 into deterministic descriptive insight and provide
a richer presentation of current usage, without reconstructing unobserved usage or introducing prediction.

## Phases

### Phase C — Historical Insight

1. Create a read-only analytical layer over the v1.3 history boundary.
2. Produce deterministic observational summaries.
3. Produce historical observation series.
4. Visualize summaries and series.
5. Preserve v1.3 discrete-observation semantics.

### Phase A — Current Visualization

Begins only after Phase C is functionally closed.

1. Improve current-state presentation.
2. Reuse presentation concepts established by Phase C.
3. Preserve stable current-window identity through the presentation boundary.
4. Allow navigation from a current window to history for the same stable `UsageWindowId`.


### Stabilization gate — GUI lifecycle

Before release close, v1.4 SHALL stabilize GUI composition discovered during target validation:

1. Current Details is composed once rather than created and replaced after base-shell construction.
2. Controller polling renders only state transitions, not every poll tick.
3. History is a sibling/top-level surface with independent show/hide polling lifecycle.
4. `History` exposes `Period` as its only visible selector in v1.4; stable window identity is internal.
5. Explicit current-to-history identity is preserved even when the selected period contains no samples.
6. Reset metadata may be explicitly shown as `not reported` without fabricating a timestamp.

## Scoped requirements

- `REQ-ANALYTICS-001` — descriptive historical usage analysis.
- `REQ-HISTORY-UI-001` — historical usage visualization.
- `REQ-UI-003` — richer current usage visualization.
- `REQ-UI-LIFECYCLE-001` — GUI composition and lifecycle stabilization.

Dependency order:

`REQ-ANALYTICS-001 -> REQ-HISTORY-UI-001 -> REQ-UI-003 -> REQ-UI-LIFECYCLE-001`

## Product intent

v1.4 is an understanding release, not a prediction release.

It may summarize and visualize values actually observed by CodexBar. It SHALL NOT convert gaps between
observations into fabricated measurements or authoritative token accounting.

## Historical periods

The historical product surface exposes:

- previous 24 hours;
- previous 7 days;
- previous 30 days.

Each request captures one timezone-aware end instant and constructs a half-open `[start, end)` interval.
These periods are not persisted as settings in v1.4.

## Architectural direction

The intended historical read path is:

`HistoryRepository -> HistoricalAnalysis -> History presentation state -> History UI`

Current monitoring remains independently composed:

`RefreshCoordinator -> TrayController -> UsageViewState -> current UI`

Historical interaction SHALL NOT turn the existing current-usage controller into a source of historical
state. A dedicated history controller/coordinator MAY be introduced when needed by the requirements.

The UI is not the source of truth for analytical calculations.

Analytics does not directly depend on SQLite or Qt.

## Persistence compatibility decision

v1.4 SHALL retain the validated v1.3 history schema version 1.

Read-side queries and indexes MAY evolve compatibly within schema v1 when required by scoped behavior, but
v1.4 SHALL NOT introduce schema v2 solely for analytics or visualization.

Any persistence-format/schema-version change requires a separate compatibility decision consistent with the
project constitution.

Settings schema v1 also remains unchanged unless a separately scoped requirement explicitly changes it.

## Read-only storage behavior

Historical analysis and visualization are read-only secondary capabilities.

Opening or querying historical views SHALL NOT create, clear, repair, migrate, append to, or otherwise
mutate the history database solely to satisfy a read request.

In particular, an absent history database SHALL remain absent until an existing write-side behavior has a
legitimate reason to create it.

## Non-goals

- prediction of exhaustion;
- prediction of LOW/EXHAUSTED;
- consumption forecasting;
- statistical trend fitting;
- authoritative usage-rate reporting;
- token-consumption estimation;
- interpolation of unobserved values;
- reconstruction of continuous usage trajectories;
- time spent LOW/EXHAUSTED;
- time-weighted statistics;
- naïve sample averages presented as time averages;
- automatic confirmation of resets from positive quota changes alone;
- configurable history retention;
- cloud or remote history;
- account-level analytics;
- raw provider archival;
- new persistent visualization settings;
- historical data as a fallback source for current usage;
- history schema v2;
- an analytics-specific ADR unless a later implementation decision introduces lasting architectural cost.

## Release sequencing

Implementation SHALL proceed in this order:

1. analytical application contracts;
2. analytical pure tests;
3. required history read-side extensions;
4. analytics acceptance tests;
5. historical presentation/view model;
6. historical asynchronous controller/coordinator;
7. historical GUI;
8. Phase C target validation;
9. current presentation-contract extension preserving stable `UsageWindowId`;
10. current GUI redesign;
11. current-to-history navigation;
12. GUI composition/lifecycle stabilization;
13. full regression and target validation;
14. release close.

No historical GUI implementation should precede closure of the analytical semantics it presents.

## Performance guards

- `PERF-GUARD-002`: history SQLite queries do not execute synchronously in the Qt GUI event path.
- `PERF-GUARD-003`: a superseded analytical request cannot replace a newer active selection.
- `PERF-GUARD-004`: rendering optimization cannot alter analytical summary values.
- `PERF-GUARD-005`: if target validation shows full 30-day rendering is impractical, presentation SHALL
  use a bounded rendering strategy without changing stored observations or analytical summaries.
- `PERF-GUARD-006`: discovering available historical windows SHALL NOT require materializing every
  historical snapshot solely to determine distinct stable window identities.

No specific downsampling algorithm is selected by this release specification.

## Release gates

Phase C is complete only when:

- all `REQ-ANALYTICS-001` acceptance criteria are traceable and passing;
- all `REQ-HISTORY-UI-001` acceptance criteria are traceable and passing;
- analytics is demonstrably read-only;
- an absent history store remains absent when history is opened for reading;
- no forecasting/interpolation path exists;
- history schema remains version 1;
- historical window discovery does not require full snapshot materialization solely for identity discovery;
- historical queries do not block the GUI;
- absent, empty, singleton, unavailable and unsupported-history states are handled;
- existing v1.3 current/history architectural invariants remain green or are explicitly strengthened without
  weakening their protected contracts;
- target historical GUI validation passes.

v1.4 closes only when additionally:

- all `REQ-UI-003` criteria pass;
- stable `UsageWindowId` survives the current presentation boundary;
- richer current presentation preserves CURRENT/STALE/error semantics;
- textual and graphical current percentages remain consistent with existing whole-percent presentation;
- existing canonical glance behavior remains compatible;
- native Ayatana and Qt fallback paths remain operational;
- current-to-history navigation uses stable window identity;
- repository-wide pytest, Ruff, strict mypy and compileall pass;
- target Ubuntu/GNOME/Wayland validation passes.

## ADR disposition

No new ADR is required by the specification as currently scoped.

The historical analytical layer follows the existing dependency rules and consumes the accepted v1.3
history boundary. An ADR SHALL be reconsidered only if implementation introduces a lasting architectural
decision such as a new persistence format/schema version, a substantial new GUI/chart framework, or another
compatibility-affecting technology choice.
