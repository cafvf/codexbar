# v1.2 Tasks

Status: alert core implementation in progress

## REQ-ALERT-001

- [x] TASK-201 review REQ-ALERT-001 against the v1.0/v1.1 architecture and resolve the Linux notification
  transport decision; ADR-006 selects freedesktop notifications through PySide6.QtDBus.
- [ ] TASK-202 complete acceptance tests for baseline, LOW/EXHAUSTED transitions, deduplication, re-arm,
  multi-window behavior, disabled notifications, stale/error behavior, restart semantics, and delivery
  failure isolation.
- [x] TASK-203 write focused unit tests for the framework-independent transition evaluator and `AlertEvent`
  contract.
- [x] TASK-204 define the notification application port and normalized delivery-failure contract.
- [x] TASK-205 implement deterministic per-window transition tracking using stable `UsageWindowId` and the
  existing `UsagePolicy`.
- [x] TASK-206 integrate `notifications_enabled` so disabled delivery still advances transition state and
  re-enable does not replay suppressed transitions.
- [ ] TASK-207 implement the QtDBus Linux desktop notification adapter without adding UI/platform
  dependencies to domain/application alert logic.
- [ ] TASK-208 wire alert evaluation/delivery into successful current refresh completion without changing
  stale/error or no-overlap semantics.
- [ ] TASK-209 add architecture/regression tests proving provider-payload isolation, settings-schema
  stability, classifier reuse, and notification-failure containment.
- [ ] TASK-210 run repository-wide pytest/ruff/mypy/compileall gates and preserve all v1.0/v1.1 tests.
- [ ] TASK-211 validate LOW, EXHAUSTED, deduplication, re-arm, disable/re-enable, restart baseline, and
  failure-safe behavior on the target Ubuntu/GNOME/Wayland workstation.
- [ ] TASK-212 close traceability, validation evidence, changelog/version metadata, and v1.2 release
  documentation before tag.
