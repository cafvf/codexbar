# CodexBar v1.8 — Plan Planning Record

Status: product planning concluded; requirements drafting is next  
Theme: Plan  
Validated implementation baseline: v1.7.0 — Diagnose  
Planning baseline: 495b91c23f6d1f65e5f596280ec39730ede7c9df

## Planning outcome

The roadmap inversion is already committed:

- v1.8 — Plan;
- v1.9 — Explore;
- v2.0 — Activity research horizon.

v1.8 is intentionally sequenced before Explore because Plan depends primarily on
capabilities already stabilized through v1.7:

- authoritative Current;
- dynamic `UsageWindowId`;
- Settings;
- existing reserve/Budget semantics;
- factual alerts;
- reset-credit safety contracts;
- responsive runtime foundations;
- diagnostics/release gates.

Plan does not require richer Historical Context exploration.

## Frozen product model

The planning review approved these central semantics:

1. Current plus explicit user settings are the only Plan authorities.
2. Existing reserve remains canonical; Plan does not create a second reserve.
3. Checkpoints are `(time_to_reset, minimum_remaining)` values per
   `UsageWindowId`.
4. Checkpoint evaluation is a step function with no interpolation.
5. The effective floor is the maximum applicable reserve/checkpoint floor.
6. Plan margin is signed.
7. Above, at and below Plan remain semantically distinct.
8. Missing reset time causes partial capability degradation, not inference.
9. Duplicate checkpoint times are invalid; non-monotonic floors are allowed.
10. Canonical checkpoint duration uses integer seconds.
11. Settings evolution is backward-compatible and does not rewrite on read.
12. Stale snapshots may be displayed but do not cause Plan side effects.
13. The only core new Plan notification is transition into below-Plan.
14. History and Historical Context cannot influence Plan.
15. Plan does not predict future compliance or exhaustion.
16. Reset credits do not alter Plan status and automatic redeem remains forbidden.
17. Budget and Control remain independent from Plan.
18. No Plan-specific historical persistence is authorized.

Detailed authoritative wording is in `PRODUCT.md` and `DECISIONS.md`.

## Scope status

`CANDIDATE-SCOPE.md` records the resolved candidate scope.

Reset-credit expiry/count-change runtime notifications remain evidence-gated and
are not required for release success.

## Next specification stage

No product implementation begins from this planning package.

The next work is to derive and freeze requirements, then proceed through:

`requirements -> acceptance criteria -> architecture -> traceability -> tasks -> implementation`

Initial requirement families are expected to cover:

- Plan evaluation;
- checkpoint policy;
- Settings persistence/migration;
- Current Details presentation;
- factual below-Plan transition notification.

The exact REQ identifiers and decomposition remain to be decided during the next
stage.
