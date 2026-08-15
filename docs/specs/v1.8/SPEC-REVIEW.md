# CodexBar v1.8 — Convergence review

Status: completed; frozen for implementation

## 1. Review result

The Plan proposal has converged from a broad feature sketch into a small extension of existing capabilities.

Frozen runtime additions:

1. pure deterministic Plan evaluator;
2. in-memory Plan breach transition tracker/service.

Everything else extends an existing owner:

- reserve -> existing `UsageReservePolicy`;
- checkpoint persistence -> existing AppSettings JSON repository;
- checkpoint editing -> existing Settings surface;
- Current comparison -> existing CurrentAccountPresenter/Current Details;
- notification delivery -> existing `NotificationPort`;
- refresh/adopt integration -> existing TrayController path.

## 2. Complexity budget

### Accepted

| Added complexity | Why it pays |
|---|---|
| neutral quantities owner | TimeToReset/FractionDelta are already cross-feature concepts; avoids duplicate Plan types |
| checkpoint policy type | required to validate explicit user policy without primitives crossing core boundary |
| pure Plan evaluator | core product behavior |
| schema v3 | unavoidable persistence evolution for user policy |
| typed checkpoint editor | avoids mini-language/parser ambiguity |
| PlanPanel | direct user-facing answer to product question |
| PlanAlertService | one actionable notification category with semantics different from LOW/EXHAUSTED |
| ADR-008 | existing governance explicitly requires compatibility decision |

### Rejected

| Proposal | Rejection reason |
|---|---|
| second reserve in Plan | duplicate truth |
| nested generic Plan policy object owning reserve | unnecessary migration/duplication |
| notification rules DSL | only one rule needed |
| Plan DB/Event Store | no durable runtime state needed |
| Plan cache/revision | evaluator is cheap/pure |
| Plan worker/executor | no blocking I/O/computation |
| Plan timer/scheduler | Plan changes only with observations/settings |
| Context/History input | violates deterministic/current authority |
| forecast/probability | out of product scope |
| monotonic policy validator | imposes inferred feasibility |
| free-text checkpoint syntax | parser/user ambiguity exceeds widget savings |
| global DI/settings-runtime rewrite | current paths already support live apply |
| broad taxonomy rename | churn without v1.8 product value |

## 3. Findings removed from the critical path after verification

### Broad `UsageError` stale fallback

Rejected as a fix.

v1.0 distinguishes transient source fallback from malformed-schema fail-closed behavior. The current difference between `LatestAccountObservationReader` stale marking and `RefreshCoordinator` source-error fallback is therefore defensible and should not be flattened.

### Startup double Settings read

Demoted.

Theoretical external-edit race exists, but the current launcher load is harnessed and no normal internal mutation occurs between the two reads. Do not widen startup APIs unless implementation reveals a zero-cost consolidation.

### Redeem enum unification

Deferred.

Real duplication, no Plan dependency.

### Removing `CurrentAccountController`

Deferred.

Dedicated tests demonstrate an existing contract; removal requires a separate use/reference audit.

## 4. Existing contract repairs retained

### Redeem refetch

Retained as mandatory existing-contract fix because `AC-REDEEM-019` requires success evidence to survive refetch failure generally.

### Duplicate normalized window IDs

Retained as source-boundary hardening because Plan policy persists by window ID and v1.0 requires malformed source data to fail through normalized error taxonomy.

### Configured LOW in account presenter

Retained only as a piggyback coherence fix when presenter already gains current Settings ownership for Plan. No separate runtime abstraction is permitted.

## 5. Test-harness review

The frozen design preserves the harness by construction:

- canonical Plan behavior is table-driven;
- Settings v3 extends, rather than duplicates, v1/v2 tests;
- Plan alerts reuse transition semantics and the same physical notification script;
- architecture boundaries use the existing AST-test style;
- post-redeem Plan uses existing `adopt_snapshot()` path;
- no Plan concurrency tests are needed because no Plan concurrency exists.

Estimated new test surface is bounded to a handful of cohesive files rather than one test/REQ.

## 6. Persistence review

Schema v3 is justified because checkpoints and Plan notification opt-in are persistent user intent.

Flat schema was chosen because it:

- keeps reserve in its existing location;
- avoids a nested “Plan” object that would imply ownership of reserve;
- preserves exact-key validation;
- makes legacy decode straightforward.

Integer seconds avoid adding a duration-string parser; persisted Plan checkpoints are explicitly whole-second coordinates so the conversion is lossless.

## 7. Alert review

Plan breach notifications remain in core v1.8 because they turn Plan into an actionable operating policy and can reuse the existing notification infrastructure.

The feature is bounded by:

- one fixed category;
- default false;
- no generic rules;
- no timer;
- no persistent alert state;
- CURRENT-only;
- no automatic mutation.

This is considered an acceptable complexity/value trade.

## 8. UI review

Budget and Plan remain semantically separate.

Plan may repeat Current percentage because the comparison should be understandable locally, but it should not repeat Budget headroom/recommendation.

The effective-floor source explains reserve interaction without creating a second reserve presentation model.

## 9. Repository hygiene review

Tracked `.omx` runtime artifacts and accidental `:1:1` files are real repository hygiene issues.

They are intentionally not Plan requirements.

Recommended disposition: separate CHORE commit with its own inspection/gate so product behavior diffs stay reviewable.

## 10. Documentation conflict protection

The root README currently contains user-local unstaged work.

No generated v1.8 package should blindly replace it.

README integration is a release requirement but must be reconciled against the local edited version at the documentation phase.

## 11. Implementation readiness

The final review is closed:

- the eight REQs and decisions are accepted;
- ADR-008 is accepted;
- no blocking contradiction was found with current v1.7 code/tests;
- exact checkpoint editor widget layout remains correctly classified as non-normative.

No further product-level question is implementation-blocking. Implementation SHALL proceed in the
phase order defined by `TASKS.md`; any stop condition below returns the affected phase to specification
review before code continues.

## 12. Stop conditions during implementation

Stop the current phase and return to spec if implementation appears to require:

- a new Plan persistence subsystem;
- a new scheduler/worker/cache;
- History/Context input;
- generic notification rules;
- automatic redeem;
- parsing semantic duration from `UsageWindowId`;
- changing Budget reserve/headroom meaning;
- changing source STALE/fail-closed semantics;
- changing checkpoint persistence shape.

Those indicate scope/design drift rather than an implementation detail.
