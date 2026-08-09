# v1.2 Tasks

Status: functional scope closed; release preparation pending

## REQ-ALERT-001

- [x] TASK-201 resolve Linux notification transport; ADR-006 documents the final `notify-send` decision.
- [x] TASK-202 complete acceptance coverage for baseline, transitions, deduplication, re-arm,
  settings, stale/error, restart semantics and delivery isolation.
- [x] TASK-203 unit-test the framework-independent transition evaluator and AlertEvent.
- [x] TASK-204 define NotificationPort and normalized delivery failures.
- [x] TASK-205 implement per-window transition tracking with UsageWindowId and UsagePolicy.
- [x] TASK-206 integrate notifications_enabled without replay on re-enable.
- [x] TASK-207 implement the Linux desktop notification adapter behind NotificationPort.
- [x] TASK-208 wire alert evaluation/delivery into completed refreshes.
- [x] TASK-209 add architecture/regression tests.
- [x] TASK-210 run repository-wide pytest/ruff/mypy/compileall gates.
- [x] TASK-211 validate alert behavior on Ubuntu/GNOME/Wayland.
- [ ] TASK-212 prepare v1.2.0 release metadata, final traceability/release review, release commit and tag.
