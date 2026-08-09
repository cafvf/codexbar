# v1.3 Tasks

Status: storage foundation complete; runtime integration pending
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
- [x] TASK-311 clear acceptance coverage, except AC-HISTORY-037 which remains explicitly pending until
  runtime integration can prove that clear does not alter current in-memory usage/alert state.

## SQLite infrastructure
- [x] TASK-312 implement canonical XDG history path resolution with Snap-scoped fallback protection.
- [x] TASK-313 implement schema-v1 SQLite initialization and validation with foreign keys enabled.
- [x] TASK-314 implement canonical UTC timestamp and Decimal serialization/round trip.
- [x] TASK-315 implement deterministic normalized observation key and idempotent append transaction.
- [x] TASK-316 implement atomic snapshot + window persistence.
- [x] TASK-317 implement indexed interval and stable-window queries.
- [x] TASK-318 implement fixed 30-day pruning with cascade and exact cutoff semantics.
- [x] TASK-319 implement inspection summary.
- [x] TASK-320 implement transactional history clear preserving schema.
- [x] TASK-321 normalize SQLite/schema/corruption failures without destructive recovery.

## Runtime integration
- [ ] TASK-322 integrate history capture only after successful CURRENT refresh completion.
- [ ] TASK-323 ensure stale fallback and provider errors never invoke history append.
- [ ] TASK-324 isolate history append/prune failures so alerts and tray/current usage continue normally.
- [ ] TASK-325 define deterministic maintenance/prune trigger without introducing a second sampling cadence.
- [ ] TRACE-GAP-001 close AC-HISTORY-037 with runtime-level evidence that `history clear` does not alter
  current in-memory usage or alert state.

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
