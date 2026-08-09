# v1.1 Tasks

Status: REQ-SETTINGS-001 complete

## REQ-SETTINGS-001

- [x] TASK-101 specify settings scope, defaults, validation domains, errors, persistence and non-goals.
- [x] TASK-102 specify UC-SETTINGS-001..006 and AC-SETTINGS-001..024.
- [x] TASK-103 write red acceptance tests for defaults, persistence, XDG isolation, corruption,
  UsagePolicy application, reset and CLI diagnostics.
- [x] TASK-104 write red unit tests for domain settings values and JSON/XDG repository behavior.
- [x] TASK-105 record persistence/compatibility decision in ADR-005.
- [x] TASK-106 implement domain `AppSettings` and validated refresh interval without persistence imports.
- [x] TASK-107 define settings port, load result/origin, and normalized settings errors.
- [x] TASK-108 implement JSON/XDG settings repository with schema-v1 validation and atomic replacement.
- [x] TASK-109 implement get/save/reset application use cases.
- [x] TASK-110 integrate configured LOW threshold with `UsagePolicy`.
- [x] TASK-111 make refresh cadence runtime-configurable without overlapping refresh operations.
- [x] TASK-112 implement `settings show` and `settings reset` CLI surfaces.
- [x] TASK-113 implement Qt settings surface with Save/Cancel/Reset and validation feedback.
- [x] TASK-114 run repository-wide pytest/ruff/mypy/compileall gates.
- [x] TASK-115 validate GUI settings lifecycle and restart persistence on target Linux workstation.
- [x] TASK-116 close traceability and release documentation for REQ-SETTINGS-001.
