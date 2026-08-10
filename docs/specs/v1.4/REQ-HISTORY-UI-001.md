# REQ-HISTORY-UI-001 — Historical usage visualization

Status: validated — v1.4.0 release candidate
Priority: P0  
Release: v1.4  
Change taxonomy: EVOLUTION

## Requirement

CodexBar SHALL provide an interactive graphical presentation of historical observations and descriptive
summaries produced by `REQ-ANALYTICS-001`.

The UI SHALL preserve the distinction between actual observations and continuous/inferred behavior.

It SHALL NOT become the source of truth for analytical calculations or mutate persistent history solely to
serve a read interaction.

## Historical availability states

The historical presentation SHALL handle at least:

- no retained observations for the selected request;
- analytical/history unavailable;
- unsupported history schema.

The v1.3 storage states `ABSENT` and `READY_EMPTY` remain distinct storage states. They MAY share a
user-facing empty-history presentation when no user action depends on distinguishing them, but opening the
view SHALL NOT create absent storage.

## UC-HISTORY-UI-001 — Open historical usage

- `AC-HISTORY-UI-001`: history can be opened from the normal desktop interface.
- `AC-HISTORY-UI-002`: opening history does not force a provider refresh solely to construct history.
- `AC-HISTORY-UI-003`: opening history does not mutate persisted history.
- `AC-HISTORY-UI-004`: default selected period is 24 hours.
- `AC-HISTORY-UI-005`: one analyzable window is selected when available.
- `AC-HISTORY-UI-006`: no analyzable windows yields a meaningful empty state.
- `AC-HISTORY-UI-006A`: when history storage is absent, opening the historical view does not create the
  history database solely to satisfy the read interaction.
- `AC-HISTORY-UI-006B`: absent history and valid-but-empty history may share an empty presentation, but the
  application/read contract does not collapse their persistent-storage semantics.

## UC-HISTORY-UI-002 — Select period

The user can select `24h | 7d | 30d`.

- `AC-HISTORY-UI-007`: 24h maps to the corresponding analytical interval.
- `AC-HISTORY-UI-008`: 7d maps to the corresponding analytical interval.
- `AC-HISTORY-UI-009`: 30d maps to the corresponding analytical interval.
- `AC-HISTORY-UI-010`: changing period replaces the previous selection.
- `AC-HISTORY-UI-011`: period selection is not persisted as a new setting.

## UC-HISTORY-UI-003 — Preserve focused usage-window identity

The v1.4 History surface exposes `Period` as its only user-selectable filter. Stable window identity remains
internal presentation state.

- `AC-HISTORY-UI-012`: History opened from a current card preserves that card's stable `UsageWindowId`.
- `AC-HISTORY-UI-013`: changing period preserves an explicitly focused stable identity.
- `AC-HISTORY-UI-014`: human label remains presentation data, not identity.
- `AC-HISTORY-UI-015`: History opened globally selects one deterministic analyzable identity when available.
- `AC-HISTORY-UI-015A`: an explicitly focused identity with no retained samples yields the standard empty
  state for that same identity; the controller SHALL NOT silently substitute another window.
- `AC-HISTORY-UI-015B`: browsing arbitrary historical-only identities is deferred beyond v1.4 and is not a
  visible selector in this release.

## UC-HISTORY-UI-004 — Show historical summary

The selected historical view SHALL show, when defined:

- observation count;
- first/latest observation time;
- first/latest remaining;
- observed minimum/maximum;
- observed change.

Acceptance criteria:

- `AC-HISTORY-UI-016`: every summary value matches the analytical read model.
- `AC-HISTORY-UI-017`: observed change is labelled as observational change, not consumption.
- `AC-HISTORY-UI-018`: undefined singleton change renders as unavailable, not zero.
- `AC-HISTORY-UI-019`: timestamps are localized only for presentation.
- `AC-HISTORY-UI-020`: values absent from analytics are not fabricated.

## UC-HISTORY-UI-005 — Plot discrete observations

Each graphical datum corresponds to one actual persisted historical observation.

- `AC-HISTORY-UI-021`: X derives from actual observation timestamp.
- `AC-HISTORY-UI-022`: Y derives from actual remaining fraction.
- `AC-HISTORY-UI-023`: Y semantics remain bounded to 0–100%.
- `AC-HISTORY-UI-024`: no point exists for an unobserved timestamp.
- `AC-HISTORY-UI-025`: observed increases remain visible and are not smoothed away.
- `AC-HISTORY-UI-026`: no forecast points are generated.
- `AC-HISTORY-UI-027`: labeling communicates that data are observations.
- `AC-HISTORY-UI-028`: rendering optimization cannot change numerical summaries.

Canonical semantics are discrete points. Any line connecting points is a presentation convention, not an
analytical interpolation contract.

## UC-HISTORY-UI-006 — Handle limited data

- `AC-HISTORY-UI-029`: zero observations yields an empty-history state, not a 0% chart.
- `AC-HISTORY-UI-030`: one observation is valid and displayable.
- `AC-HISTORY-UI-031`: sparse observations do not trigger interpolation.
- `AC-HISTORY-UI-032`: actual first/latest observation times are visible.

## UC-HISTORY-UI-007 — Handle history failure

- `AC-HISTORY-UI-033`: unreadable/corrupt history yields a history-specific unavailable state.
- `AC-HISTORY-UI-034`: unsupported schema yields an explicit history-specific state.
- `AC-HISTORY-UI-035`: history failure does not remove current tray usage.
- `AC-HISTORY-UI-036`: history failure does not terminate the tray application.
- `AC-HISTORY-UI-037`: UI does not silently replace/reset/migrate the database.

## UC-HISTORY-UI-008 — Remain responsive

- `AC-HISTORY-UI-038`: history retrieval does not block the Qt GUI event path.
- `AC-HISTORY-UI-039`: stale completion from an older request cannot replace a newer selection.
- `AC-HISTORY-UI-040`: closing history during an outstanding request does not crash.
- `AC-HISTORY-UI-041`: current usage refresh continues independently while history is open.
- `AC-HISTORY-UI-042`: historical orchestration does not require adding history-read responsibilities to
  the existing `TrayController` current-refresh contract.

## Architectural invariants

- `INV-HISTORY-UI-001`: UI imports no SQLite implementation.
- `INV-HISTORY-UI-002`: UI does not calculate application-owned analytical summaries.
- `INV-HISTORY-UI-003`: chart rendering consumes immutable/read-only presentation data.
- `INV-HISTORY-UI-004`: visualization cannot mutate settings, alerts or current snapshot state.
- `INV-HISTORY-UI-005`: history query work remains outside the GUI thread.
- `INV-HISTORY-UI-006`: headless CodexBar remains usable without GUI dependencies.
- `INV-HISTORY-UI-007`: the existing current `TrayController` remains free of direct history-storage
  dependencies; historical reads use a separate application/presentation orchestration path.

## Primary test specification

Acceptance: `tests/acceptance/test_req_history_ui_001.py`

Required scenarios:

1. open history with data;
2. open history when persistent history is absent and verify no database is created;
3. open valid-but-empty history;
4. switch 24h/7d/30d;
5. preserve focused identity across 24h/7d/30d and verify no visible Window selector;
6. singleton history;
7. analytical/history unavailable state;
8. unsupported-schema state;
9. observed increase retained visually without “confirmed reset” inference;
10. out-of-order async completion cannot overwrite newer selection;
11. close view during outstanding request;
12. current refresh continues while history is open;
13. focused identity absent in the selected period remains EMPTY for that identity.

Presentation-model unit tests:
`tests/unit/test_history_view_model.py`

Prefer deterministic presentation-contract tests over pixel-perfect screenshot tests.

Architecture guards SHALL preserve the protected intent of the existing v1.3 rule that current
`TrayController` does not depend on history storage.
