# REQ-SETTINGS-001 — Traceability and closure

Status: closed
Validated implementation commit: `69e15887350d5747e888625936df52931f18f9c5`
Target environment: Ubuntu / GNOME / Wayland
Release: v1.1

## Validation summary

Automated quality evidence reported on the target checkout:

- `uv run pytest -ra` -> 129 passing tests before the Ayatana menu correction;
- subsequent native-settings correction preserved the requirement behavior and was validated on the
  target workstation;
- `uv run ruff check src tests` -> passed;
- `uv run mypy` -> passed;
- `uv run python -m compileall -q src` -> passed.

Manual target validation covered the complete GUI lifecycle:
open current values, Save, live runtime application, Cancel, invalid-value feedback, Reset, persistence
after restart, and final restoration. During target validation an integration defect was found: the native
Ayatana menu did not initially expose `Settings`. The native helper contract and menu were corrected, and
the Settings action was then available through the active native backend.

The refresh interval was also explicitly reconciled with the specification: the supported interval is
inclusive `10..3600` seconds. Accepting values around 3500 is correct product behavior; 3601 is the first
invalid integer above the upper bound.

## Acceptance-criteria traceability

| Acceptance criteria | Evidence | Disposition |
|---|---|---|
| AC-SETTINGS-001..006 | settings acceptance tests; JSON/XDG repository tests; corruption fallback tests | PASS |
| AC-SETTINGS-007..011 | persistence/unit tests; validation and atomic-write behavior | PASS |
| AC-SETTINGS-012 | configured `UsagePolicy` controller/ViewModel tests and live GUI application | PASS |
| AC-SETTINGS-013 | timer integration tests plus target live-cadence validation without process restart | PASS |
| AC-SETTINGS-014 | `notifications_enabled` persisted/exposed with no delivery side effect | PASS |
| AC-SETTINGS-015..017 | reset tests including idempotence and preservation of neighboring files | PASS |
| AC-SETTINGS-018 | `settings show` CLI tests and target inspection | PASS |
| AC-SETTINGS-019 | `settings reset` CLI tests and shared `ResetSettings` application use case | PASS |
| AC-SETTINGS-020 | Qt settings-dialog test and target open-current-values validation | PASS |
| AC-SETTINGS-021 | Qt Save test; persistence; runtime threshold/cadence application; target validation | PASS |
| AC-SETTINGS-022 | Qt Cancel test and target validation | PASS |
| AC-SETTINGS-023 | Qt Reset test using shared application use case and target validation | PASS |
| AC-SETTINGS-024 | Qt invalid-input tests and target validation with dialog remaining open | PASS |

## Invariant traceability

| Invariant | Evidence | Disposition |
|---|---|---|
| INV-SETTINGS-001 | domain settings implementation has no UI/infrastructure imports | PASS |
| INV-SETTINGS-002 | architecture invariant tests; JSON/XDG handling remains outside domain/application | PASS |
| INV-SETTINGS-003 | `AppSettings -> UsagePolicy -> UsageViewModel` runtime path; no duplicate policy | PASS |
| INV-SETTINGS-004 | settings only expose notification enablement; delivery remains deferred | PASS |

## Closure

All TASK-101..116 are complete. REQ-SETTINGS-001 is accepted for v1.1.

Any future change to the persistence schema requires an ADR and explicit compatibility behavior.
Notification delivery remains outside this requirement and belongs to `REQ-ALERT-001`.
