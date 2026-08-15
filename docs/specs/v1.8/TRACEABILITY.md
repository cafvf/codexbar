# CodexBar v1.8 — Implementation traceability

Status: implementation complete; release preparation
Theme: Plan
Baseline release: v1.7.0 — Diagnose
Release candidate: v1.8.0

This matrix closes the frozen `REQ-PLAN-*`, `UC-1801..1809`, `AC-1801..1838` and `INV-PLAN-*` contracts against the implementation and evidence that actually shipped into the v1.8 release-preparation branch.

## Acceptance-criterion closure

| AC | Requirement / use case | Primary implementation | Primary automated evidence | Additional evidence | Status |
|---|---|---|---|---|---|
| AC-1801 | REQ-PLAN-001 / UC-1801 | `domain/settings.py`, `ui/settings.py` | `tests/unit/test_plan.py`, `tests/unit/test_plan_settings_ui.py` | Settings target validation | covered |
| AC-1802 | REQ-PLAN-001 / UC-1801 | `UsagePlanCheckpoint`, `UsagePlanCheckpointPolicy` | `tests/unit/test_plan.py`, `tests/unit/test_settings_schema_v3.py` | P12/non-monotonic coverage | covered |
| AC-1803 | REQ-PLAN-004 / UC-1801 | `SettingsDialog`, `SettingsActions` | `tests/unit/test_plan_settings_ui.py`, `tests/gui/test_settings_dialog.py` | Save/Cancel/Reset physically validated | covered |
| AC-1804 | REQ-PLAN-003/004 / UC-1801 | immutable `AppSettings` updates, Settings editor | `tests/unit/test_settings_models.py`, `tests/unit/test_plan_settings_ui.py` | absent-window preservation exercised | covered |
| AC-1805 | REQ-PLAN-002 / UC-1802 | `evaluate_window_plan()` | `tests/unit/test_plan.py` | P03–P14 factual-coordinate vectors | covered |
| AC-1806 | REQ-PLAN-002 / UC-1802 | stepwise checkpoint selector | `tests/unit/test_plan.py` | P03/P04/P05/P14 | covered |
| AC-1807 | REQ-PLAN-002 / UC-1802 | effective-floor calculation | `tests/unit/test_plan.py` | P06/P07/P08 | covered |
| AC-1808 | REQ-PLAN-002 / UC-1802 | `FractionDelta`, `PlanCompliance` | `tests/unit/test_plan.py` | P02/P04/P05/P06/P07/P08 | covered |
| AC-1809 | REQ-PLAN-002 / UC-1803 | `NOT_CONFIGURED` result | `tests/unit/test_plan.py` | P01 | covered |
| AC-1810 | REQ-PLAN-002 / UC-1803 | `NO_ACTIVE_CHECKPOINT` result | `tests/unit/test_plan.py` | P03/P13 | covered |
| AC-1811 | REQ-PLAN-002 / UC-1803 | `RESET_MISSING`, `RESET_INVALID` | `tests/unit/test_plan.py` | P09/P10/P11 | covered |
| AC-1812 | REQ-PLAN-002 / UC-1803 | nullable floor/margin/compliance | `tests/unit/test_plan.py` | P01/P03/P10 | covered |
| AC-1813 | REQ-PLAN-003 / UC-1804 | `JsonSettingsRepository` schema 3 | `tests/unit/test_settings_schema_v3.py` | canonical round-trip vectors | covered |
| AC-1814 | REQ-PLAN-003 / UC-1804 | schema 1/2 readers + schema 3 writer | `tests/unit/test_settings_schema_v1_migration.py`, `tests/unit/test_settings_schema_v2.py`, `tests/unit/test_settings_schema_v3.py` | no-rewrite/read then explicit-save coverage | covered |
| AC-1815 | REQ-PLAN-003 / UC-1804 | typed settings-document validation | `tests/unit/test_settings_schema_v3.py`, `tests/unit/test_settings_repository.py` | S06–S08 invalid vectors | covered |
| AC-1816 | REQ-PLAN-004 / UC-1804 | `codexbar settings show` | `tests/unit/test_cli.py` | schema/origin/checkpoint rendering | covered |
| AC-1817 | REQ-PLAN-003/004 / UC-1804 | functional `AppSettings` updates | `tests/unit/test_settings_models.py`, `tests/unit/test_plan_settings_ui.py` | unrelated-field preservation | covered |
| AC-1818 | REQ-PLAN-005/007 / UC-1805 | `CurrentAccountPresenter` | `tests/unit/test_plan_current_presentation.py`, `tests/unit/test_current_account_viewmodel.py` | no second source read | covered |
| AC-1819 | REQ-PLAN-005 / UC-1805 | `PlanViewState`, `PlanPanel` | `tests/unit/test_plan_panel_text.py`, `tests/gui/test_plan_panel.py` | PlanPanel target validation | covered |
| AC-1820 | REQ-PLAN-005 / UC-1805 | STALE presentation guard | `tests/unit/test_plan_current_presentation.py`, `tests/gui/test_plan_panel.py` | no current compliance claim when stale | covered |
| AC-1821 | REQ-PLAN-005/008 / UC-1805 | existing Budget remains separate | `tests/unit/test_budget_policy.py`, `tests/architecture/test_v18_plan_architecture.py` | physical 15% Budget vs 90% Plan check | covered |
| AC-1822 | REQ-PLAN-006 / UC-1806 | `PlanAlertService` tracker | `tests/unit/test_plan_alerts.py` | A01–A03; physical breach/rearm | covered |
| AC-1823 | REQ-PLAN-006 / UC-1806 | CURRENT-only alert gate | `tests/unit/test_plan_alerts.py` | A09 | covered |
| AC-1824 | REQ-PLAN-006 / UC-1806 | delivery gates outside tracker identity | `tests/unit/test_plan_alerts.py` | A04; physical disabled/no-replay | covered |
| AC-1825 | REQ-PLAN-006 / UC-1806 | notification-delivery isolation | `tests/unit/test_plan_alerts.py` | notifier failure vector | covered |
| AC-1826 | REQ-PLAN-006 / UC-1806 | per-window tracker state | `tests/unit/test_plan_alerts.py` | A10 | covered |
| AC-1827 | REQ-PLAN-006 / UC-1807 | checkpoint activation transition | `tests/unit/test_plan_alerts.py` | A05; physical activation | covered |
| AC-1828 | REQ-PLAN-006 / UC-1807 | policy fingerprint/rebaseline | `tests/unit/test_plan_alerts.py` | A06 | covered |
| AC-1829 | REQ-PLAN-006 / UC-1807 | resolved reset-cycle key | `tests/unit/test_plan_alerts.py` | A07 | covered |
| AC-1830 | REQ-PLAN-006 / UC-1807 | unresolved checkpoint-capability guard | `tests/unit/test_plan_alerts.py` | A08 | covered |
| AC-1831 | REQ-PLAN-007 / UC-1808 | `TrayController._state_from_snapshot()` / `adopt_snapshot()` | `tests/unit/test_plan_alert_runtime_controller.py` | refresh and post-redeem convergence | covered |
| AC-1832 | REQ-PLAN-007 / UC-1808 | redeem successful-consume refetch boundary | `tests/unit/test_redeem_process_manager.py` | expected `UsageError` refetch regression | covered |
| AC-1833 | REQ-PLAN-008 / UC-1809 | Plan core dependency boundaries | `tests/architecture/test_v18_plan_architecture.py` | INV-PLAN-001 | covered |
| AC-1834 | REQ-PLAN-008 / UC-1809 | Budget + legacy alerts unchanged | `tests/unit/test_budget_policy.py`, `tests/unit/test_alerts.py`, `tests/unit/test_alert_validation_harness.py` | legacy physical alert scenarios green | covered |
| AC-1835 | REQ-PLAN-008 / UC-1809 | no Plan-to-redeem/reset-ledger authority | `tests/architecture/test_v18_plan_architecture.py`, `tests/architecture/test_no_automatic_redeem.py` | INV-PLAN-004 | covered |
| AC-1836 | REQ-PLAN-008 / UC-1809 | opaque `UsageWindowId` in Plan core | `tests/architecture/test_v18_plan_architecture.py`, `tests/unit/test_plan.py` | INV-PLAN-007 | covered |
| AC-1837 | REQ-PLAN-008 / UC-1809 | no predictive Plan surface | `tests/architecture/test_v18_plan_architecture.py` | source/spec review | covered |
| AC-1838 | REQ-PLAN-008 / UC-1809 | protected v1.0–v1.7 regression families | full `pytest` suite + existing architecture/GUI/acceptance families | pre-release-prep gate: 815 passed | covered; final release gate pending |

## Requirement closure

| Requirement | Covered by | Status |
|---|---|---|
| REQ-PLAN-001 | AC-1801..1804 plus checkpoint model tests | implemented |
| REQ-PLAN-002 | AC-1805..1812, P01..P14 | implemented |
| REQ-PLAN-003 | AC-1813..1817, S01..S08 | implemented |
| REQ-PLAN-004 | AC-1801..1804, AC-1816..1817 | implemented and physically validated |
| REQ-PLAN-005 | AC-1818..1821 | implemented and physically validated |
| REQ-PLAN-006 | AC-1822..1830, A01..A10 | implemented and physically validated |
| REQ-PLAN-007 | AC-1818, AC-1831..1832 | implemented |
| REQ-PLAN-008 | AC-1833..1838 | protected; final full release gate pending |

## Architectural invariants

| Invariant | Evidence | Status |
|---|---|---|
| INV-PLAN-001 — no Context/History authority | `tests/architecture/test_v18_plan_architecture.py` import/AST checks | protected |
| INV-PLAN-002 — no Plan persistence subsystem | architecture path/import checks; Settings remains checkpoint persistence owner | protected |
| INV-PLAN-003 — no Plan concurrency subsystem | architecture import/source checks | protected |
| INV-PLAN-004 — no Plan-to-redeem mutation | architecture checks + existing no-auto-redeem gate | protected |
| INV-PLAN-005 — reserve has one owner | checkpoint field-shape assertion + settings model | protected |
| INV-PLAN-006 — Budget remains Plan-independent | Budget import/source assertion + released budget vectors | protected |
| INV-PLAN-007 — opaque window identity | string/import checks + opaque-ID unit vectors | protected |

## Physical evidence already completed

On target Ubuntu/GNOME/Wayland:

- Settings add/edit/remove checkpoints, Save/reopen, Cancel and Reset behaved as specified;
- Plan breach notification opt-in persisted and reapplied without restart;
- PlanPanel rendered in Current Details between Control/Budget and Reset action;
- a 30-day checkpoint rendered as `30d` while the normative 72-hour coordinate renders as `72h`;
- Budget remained reserve-only when Plan checkpoint floor differed materially from the reserve;
- Plan breach, recovery/rearm, disabled/no-replay and checkpoint-activation notification scenarios passed;
- existing LOW/dedupe/disabled/multi-window notification scenarios remained green;
- no real reset credit was consumed.

Native Ayatana/Qt fallback remains a protected product contract. v1.8 changes do not replace that architecture. A destructive package-removal exercise is not required merely to force fallback; final Phase-F target smoke records what can be safely exercised on the target.

## Release closure still required

This file establishes implementation traceability, not release publication. Remaining release gates are tracked in `docs/RELEASE-CHECKLIST-v1.8.0.md` and include:

1. regenerate and verify `uv.lock` after the 1.8.0 version bump;
2. final post-bump local gate;
3. release-version validation in uv-run, editable and isolated uv-tool modes;
4. deliberate reconciliation of the user-owned root `README.md`;
5. exact release-prep commit/push;
6. hosted Python 3.12/3.13/3.14 and uv-tool CI success on that exact commit;
7. annotated `v1.8.0` tag creation/push/remote verification.
