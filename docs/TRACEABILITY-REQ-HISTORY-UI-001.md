# REQ-HISTORY-UI-001 — Traceability and closure

Status: validated / closed for v1.4.0 release candidate
As-built refinement: History exposes **Period only**; stable `UsageWindowId` is internal/focused state.

| Contract area | Acceptance criteria | Primary implementation | Primary evidence | Disposition |
|---|---|---|---|---|
| open/empty/absent | AC-001..006B | `ui/history_controller.py`, `ui/history_dialog.py` | `test_req_history_ui_001.py` | PASS |
| period selection | AC-007..011 | History controller/dialog | history UI acceptance + time-axis tests | PASS |
| focused identity | AC-012..015B | History controller/dialog | period-only + focused-empty lifecycle tests | PASS |
| summary | AC-016..020 | history view model/dialog | `test_history_view_model.py` | PASS |
| discrete chart/time axis | AC-021..028 | History chart/presentation state | history UI + time-axis acceptance | PASS |
| limited/sparse data | AC-029..032 | presentation model | unit + acceptance | PASS |
| unavailable/unsupported | AC-033..037 | controller/view-state mapping | acceptance/failure tests | PASS |
| responsiveness/lifecycle | AC-038..042 | dedicated HistoryController + top-level dialog | lifecycle stabilization tests + target validation | PASS |
| architecture | INV-001..007 | UI/application boundaries | v1.4 architecture guards | PASS |

Arbitrary historical-only window browsing is explicitly deferred beyond v1.4; analytics still discovers those identities.
