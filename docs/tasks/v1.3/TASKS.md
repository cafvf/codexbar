# v1.3 Tasks

Status: release close pending
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
- [x] TASK-322 capture history in the refresh worker path after a successful provider observation.
- [x] TASK-323 ensure provider failure/STALE fallback never creates a second historical observation.
- [x] TASK-324 isolate append/prune failures from tray/current usage and alerts.
- [x] TASK-325 perform pruning in the same CURRENT worker maintenance cycle; no second scheduler cadence.
- [x] TRACE-GAP-001 / AC-HISTORY-037 closed with runtime evidence.

## CLI/composition
- [x] TASK-326 add minimal `history inspect` CLI.
- [x] TASK-327 add explicit destructive `history clear` CLI and canonical SQLite runtime composition.
- [x] PERF-GUARD-001 history SQLite I/O runs in the existing refresh worker path, not `TrayController.poll()`.

## Architecture/regression
- [x] TASK-328 automated evidence for INV-HISTORY-001..008 plus GUI-thread storage guard.
- [x] TASK-329 explicit v1.0-v1.2 regression evidence.
- [x] TASK-330 complete pytest/ruff/mypy/compileall gate passed before target validation.

## Target validation/release
- [x] TASK-331 execute and record `docs/VALIDATION-REQ-HISTORY-001.md` on Ubuntu/GNOME/Wayland.
- [ ] TASK-332 close traceability, validation evidence, changelog/version metadata and v1.3.0 release.
