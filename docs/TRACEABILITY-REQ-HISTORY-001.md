# Traceability — REQ-HISTORY-001

Status: closed
Release: v1.3
Requirement: `docs/specs/v1.3/REQ-HISTORY-001.md`
Architecture: `docs/adr/ADR-007-history-persistence.md`

## Acceptance-criterion traceability

| Requirement area | Criteria | Primary automated evidence | Primary implementation | Status |
|---|---|---|---|---|
| CURRENT capture / atomic normalized persistence | AC-HISTORY-001..007 | `tests/acceptance/test_req_history_001_capture_query.py`, history contract/core unit tests | `application/history.py`, `infrastructure/history_sqlite.py` | validated |
| Restart persistence / no implicit insert | AC-HISTORY-008..010 | capture/query acceptance tests | `SqliteHistoryRepository` | validated |
| Deterministic `[start,end)` queries | AC-HISTORY-011..017 | `test_req_history_001_capture_query.py`, contract tests | history read models + SQLite indexed queries | validated |
| Fixed 30-day retention | AC-HISTORY-018..023 | `test_req_history_001_retention_schema.py`, `scripts/validate_history.py` | `SqliteHistoryRepository.prune` | validated |
| Failure/schema/corruption isolation | AC-HISTORY-024..028 | retention/schema tests, runtime tests, failure unit tests, validation harness | history error taxonomy, SQLite adapter, `HistoryService` | validated |
| Inspection | AC-HISTORY-029..032 | `test_req_history_001_inspect_clear.py`, history CLI tests | `inspect_path`, `inspect`, CLI `history inspect` | validated |
| Explicit clear | AC-HISTORY-033..038 | inspect/clear acceptance tests, runtime AC-037 test, CLI tests, target validation | SQLite `clear`, CLI `history clear` | validated |

## Architectural-invariant traceability

| Invariant | Evidence | Protected contract |
|---|---|---|
| INV-HISTORY-001 | `tests/acceptance/test_history_architecture_invariants.py` | domain has no SQLite/filesystem/infrastructure dependency |
| INV-HISTORY-002 | same | history application logic has no Qt/UI/SQLite implementation dependency |
| INV-HISTORY-003 | same | current usage is not reconstructed from history |
| INV-HISTORY-004 | same + runtime acceptance | STALE never becomes a new observation |
| INV-HISTORY-005 | same + `tests/unit/test_history_regressions.py` | settings schema v1 remains independent |
| INV-HISTORY-006 | same + history contract tests | SQLite consumes normalized history/domain values only |
| INV-HISTORY-007 | same + runtime failure tests | history failure stays outside provider refresh success/failure semantics |
| INV-HISTORY-008 | same + schema/corruption/clear tests | clear is never implicit corruption recovery |

Additional implementation guard:
- `PERF-GUARD-001`: history SQLite I/O is absent from `TrayController.poll()` and runs through
  `HistoryCapturingUsageProvider` in the existing refresh worker path.

## Evidence locations

Acceptance:
- `tests/acceptance/test_req_history_001_capture_query.py`
- `tests/acceptance/test_req_history_001_retention_schema.py`
- `tests/acceptance/test_req_history_001_inspect_clear.py`
- `tests/acceptance/test_req_history_001_runtime.py`
- `tests/acceptance/test_history_architecture_invariants.py`

Unit/regression:
- `tests/unit/test_history_contracts.py`
- `tests/unit/test_history_sqlite_core.py`
- `tests/unit/test_history_sqlite_failures.py`
- `tests/unit/test_history_sqlite_inspect_clear.py`
- `tests/unit/test_history_paths.py`
- `tests/unit/test_history_runtime.py`
- `tests/unit/test_history_cli.py`
- `tests/unit/test_history_regressions.py`

Target/reproducible validation:
- `scripts/validate_history.py`
- `docs/VALIDATION-REQ-HISTORY-001.md`

Implementation:
- `src/codexbar/application/history.py`
- `src/codexbar/application/history_runtime.py`
- `src/codexbar/infrastructure/history_paths.py`
- `src/codexbar/infrastructure/history_sqlite.py`
- `src/codexbar/__main__.py`

## Compatibility conclusions

- settings schema remains version 1 with no history fields;
- history schema is independently versioned as 1;
- v1.0 CURRENT/STALE behavior remains the source of truth for current usage;
- v1.2 alert state remains in memory and is not reset by history clear;
- no raw provider payload, credential or account identifier crosses the history boundary;
- corrupt/unsupported history fails closed;
- the validated v1.3 behavior is fully traceable and release metadata is aligned to 1.3.0.

REQ-HISTORY-001 is behaviorally closed and target-validated.
