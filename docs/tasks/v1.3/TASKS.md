# v1.3 Tasks

Status: runtime history integration complete; CLI/architecture validation pending
Requirement: REQ-HISTORY-001
ADR: ADR-007

## Specification/architecture
- [x] TASK-301 close REQ-HISTORY-001 behavioral decisions.
- [x] TASK-302 accept ADR-007.

## Domain/application contracts
- [x] TASK-303 define normalized historical value/result types.
- [x] TASK-304 define history application ports.
- [x] TASK-305 define normalized history error taxonomy.

## Acceptance tests first
- [x] TASK-306 capture/restart acceptance coverage.
- [x] TASK-307 query acceptance coverage.
- [x] TASK-308 retention acceptance coverage.
- [x] TASK-309 schema/corruption failure acceptance coverage.
- [x] TASK-310 inspection acceptance coverage.
- [x] TASK-311 clear acceptance coverage, including AC-HISTORY-037 runtime evidence.

## SQLite infrastructure
- [x] TASK-312 canonical XDG history path resolution.
- [x] TASK-313 schema-v1 SQLite initialization/validation.
- [x] TASK-314 UTC timestamp and Decimal round trip.
- [x] TASK-315 deterministic observation-key idempotency.
- [x] TASK-316 atomic snapshot/window persistence.
- [x] TASK-317 indexed interval/window queries.
- [x] TASK-318 fixed 30-day pruning.
- [x] TASK-319 inspection summary.
- [x] TASK-320 transactional clear.
- [x] TASK-321 normalized storage failures.

## Runtime integration
- [x] TASK-322 integrate history capture after successful refresh completion.
- [x] TASK-323 ensure STALE/provider failure never produces a new historical observation.
- [x] TASK-324 isolate append/prune failures from tray/current usage and alerts.
- [x] TASK-325 perform pruning in the same CURRENT maintenance cycle; no second sampling/scheduler cadence.
- [x] TRACE-GAP-001 close AC-HISTORY-037 with runtime evidence that history clear leaves current state and
  alert deduplication state unchanged.

## CLI
- [ ] TASK-326 add minimal history inspection CLI.
- [ ] TASK-327 add explicit destructive `history clear` CLI with documented semantics and exit codes.

## Architecture/regression
- [ ] TASK-328 add INV-HISTORY-001..008 architecture tests.
- [ ] TASK-329 verify settings schema v1 and all v1.0-v1.2 contracts remain unchanged.
- [ ] TASK-330 run complete pytest/ruff/mypy/compileall gates.

## Target validation/release
- [ ] TASK-331 validate persistence across restart, 30-day retention boundary, inspection, clear and
  history-failure isolation on Ubuntu/GNOME/Wayland.
- [ ] TASK-332 close traceability, validation evidence, changelog/version metadata and v1.3.0 release.
