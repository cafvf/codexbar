# REQ-UI-003 — Traceability and closure

Status: validated / closed for v1.4.0 release candidate

| Contract area | Acceptance criteria | Primary implementation | Primary evidence | Disposition |
|---|---|---|---|---|
| richer CURRENT cards | AC-034..040A | `ui/viewmodel.py`, `ui/current_panel.py` | current-details acceptance | PASS |
| freshness/age | AC-041..045 | current panel + normalized snapshot time | current-details/lifecycle tests | PASS |
| reset presentation | AC-046..050 | current panel | reset formatting acceptance + target validation | PASS |
| CURRENT -> History | AC-051..054A | stable `UsageWindowId` presentation/navigation | navigation + focused-empty tests | PASS |
| tray/Ayatana compatibility | AC-055..059 | tray/native-indicator boundaries | regressions + target native validation | PASS |
| GUI lifecycle | AC-060..064 | tray/current/history composition | lifecycle stabilization acceptance + target validation | PASS |
| architecture | INV-001..011 | UI/application/native boundaries | architecture invariants | PASS |

Whole-percent CURRENT presentation remains compatible with earlier releases; analytical/history Decimal semantics remain separate.
