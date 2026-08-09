# v1.3 Tasks

Status: contracts in progress
Requirement: REQ-HISTORY-001
ADR: ADR-007

Tasks derive from `REQ-HISTORY-001` acceptance criteria and architectural invariants.

## Specification/architecture

- [x] TASK-301 close REQ-HISTORY-001 behavioral decisions: 30-day retention, SQLite, `[start,end)`,
  explicit history clear and persistence of every eligible CURRENT snapshot.
- [x] TASK-302 accept ADR-007 covering SQLite schema, XDG data path, transactions, idempotency, schema
  compatibility, corruption policy, retention and clear semantics.

## Domain/application contracts

- [x] TASK-303 define normalized historical value/result types needed for query and inspection without
  introducing SQLite/UI dependencies.
- [x] TASK-304 define history application ports for append, interval query, per-window query, prune,
  inspection and clear.
- [x] TASK-305 define normalized history error taxonomy and failure-containment contracts.

## Acceptance tests first

- [ ] TASK-306 add acceptance tests for AC-HISTORY-001..010: CURRENT capture, atomic multi-window persistence,
  stale/error exclusion, normalized-data boundary, round trip, distinct observation timestamps and restart.
- [ ] TASK-307 add acceptance tests for AC-HISTORY-011..017: chronological `[start,end)` queries,
  window-id filtering, historical labels, empty results and timezone validation.
- [ ] TASK-308 add acceptance tests for AC-HISTORY-018..023: 30-day retention boundary, idempotency,
  cascade integrity and settings-schema independence.
- [ ] TASK-309 add acceptance tests for AC-HISTORY-024..028: write/read/prune failure isolation,
  unknown schema and corruption behavior.
- [ ] TASK-310 add acceptance tests for AC-HISTORY-029..032: absent/empty/non-empty/unreadable inspection.
- [ ] TASK-311 add acceptance tests for AC-HISTORY-033..038: explicit clear, schema preservation,
  empty idempotency, settings/runtime isolation and corrupt-store refusal.

## SQLite infrastructure

- [ ] TASK-312 implement canonical XDG history path resolution with Snap-scoped fallback protection.
- [ ] TASK-313 implement schema-v1 SQLite initialization and validation with foreign keys enabled.
- [ ] TASK-314 implement canonical UTC timestamp and Decimal serialization/round trip.
- [ ] TASK-315 implement deterministic normalized observation key and idempotent append transaction.
- [ ] TASK-316 implement atomic snapshot + window persistence.
- [ ] TASK-317 implement indexed interval and stable-window queries.
- [ ] TASK-318 implement fixed 30-day pruning with cascade and exact cutoff semantics.
- [ ] TASK-319 implement inspection summary.
- [ ] TASK-320 implement transactional history clear preserving schema.
- [ ] TASK-321 normalize SQLite/filesystem/schema/corruption failures without destructive recovery.

## Runtime integration

- [ ] TASK-322 integrate history capture only after successful CURRENT refresh completion.
- [ ] TASK-323 ensure stale fallback and provider errors never invoke history append.
- [ ] TASK-324 isolate history append/prune failures so alerts and tray/current usage continue normally.
- [ ] TASK-325 define deterministic maintenance/prune trigger without introducing a second sampling cadence.

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
