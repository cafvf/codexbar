# CodexBar v1.8 — Plan

Status: product semantics frozen for requirements drafting  
Theme: Plan  
Validated implementation baseline: v1.7.0 — Diagnose

## 1. Product intent

CodexBar v1.8 introduces an explicit user-defined operating plan for each dynamic
Codex usage window.

The release answers:

> How does Current compare with the plan I explicitly configured for this window?

Plan is a deterministic comparison between:

- authoritative Current facts; and
- explicit user policy.

Plan is not forecasting and does not infer intent from History, Historical Context,
usage rate, labels, window duration guesses or prior cycles.

## 2. Product authority model

The authority boundaries are:

- **Current**: authoritative observed usage state;
- **Settings / explicit Plan policy**: authoritative user intent;
- **History**: observational evidence only;
- **Historical Context**: descriptive comparison only;
- **Budget / Control**: independent deterministic control capabilities;
- **Plan**: deterministic comparison of Current against explicit user intent.

History and Historical Context do not participate in Plan evaluation.

Plan does not become authority for Current, Budget, Control, alerts unrelated to
Plan, or reset-credit redemption.

## 3. Existing reserve remains canonical

v1.5 already defines a per-`UsageWindowId` remaining-quota reserve through
`UsageReservePolicy`.

v1.8 does not introduce a second reserve concept.

The existing reserve remains canonical for static quota preservation. Plan may
compose that reserve with checkpoint policy, but must not duplicate it under a
second independently configurable `reserve_floor`.

Budget retains its existing meaning and contracts.

## 4. Checkpoint policy

A checkpoint expresses an explicit operating target for one `UsageWindowId`.

Conceptually, each checkpoint contains:

- `time_to_reset`;
- `minimum_remaining`.

Example:

- 120 h to reset -> minimum remaining 80%;
- 72 h to reset -> minimum remaining 55%;
- 24 h to reset -> minimum remaining 20%.

`time_to_reset` is a duration relative to the factual reset time. It is not an
absolute wall-clock timestamp and does not encode a fixed "5h", "weekly" or other
human alias in the domain.

## 5. Active-checkpoint semantics

Checkpoint policy is a step function.

For current factual time-to-reset `t`, a checkpoint with threshold `t_i` is reached
when:

`t <= t_i`

Among reached checkpoints, the active checkpoint is the one with the smallest
`t_i`.

Equivalently, the active checkpoint is the most recently crossed checkpoint as the
reset approaches.

Between checkpoints:

- the active floor remains unchanged;
- no interpolation is performed;
- no rate of consumption is inferred.

Example:

- 120 h -> 80%;
- 72 h -> 55%;
- 24 h -> 20%.

At 90 h to reset, the 120 h checkpoint is active.  
At 50 h to reset, the 72 h checkpoint is active.  
At 12 h to reset, the 24 h checkpoint is active.

If no checkpoint has yet been reached, no checkpoint floor is active.

## 6. Effective floor

For an evaluable Current window, Plan combines only applicable explicit policy
components.

If both a reserve and active checkpoint floor are available:

`effective_floor = max(reserve, active_checkpoint_floor)`

If only one is available, that component is the effective floor.

If neither is available, there is no applicable Plan floor.

This rule ensures that checkpoint policy never silently weakens an existing
configured reserve.

## 7. Signed margin and status

For Current remaining `R` and effective floor `F`:

`margin = R - F`

Margin is signed and is presented naturally in percentage points.

Core semantic outcomes when an effective floor exists:

- `ABOVE_PLAN` when `R > F`;
- `AT_PLAN` when `R == F`;
- `BELOW_PLAN` when `R < F`.

`NO_PLAN` is reserved for the absence of both reserve and checkpoint policy for
that `UsageWindowId`.

If checkpoint policy exists but its first checkpoint has not yet been reached and
no reserve exists, CodexBar must distinguish "Plan configured, no floor active yet"
from `NO_PLAN`. Likewise, policy that exists but cannot be evaluated because reset
time is unavailable is not `NO_PLAN`.

`AT_PLAN` is compliant with policy.

The exact Python enum/type names and final user-facing wording for pending or
unavailable assessment states are not frozen by this product document.

## 8. Partial capability and reset-time absence

`UsageWindow.resets_at` is a factual upstream capability and may be unavailable.

When reset time is unavailable:

- Current remaining remains usable if otherwise Current;
- existing reserve remains evaluable;
- checkpoint selection is unavailable;
- CodexBar must not infer reset time from `UsageWindowId`, label, History or prior
  cycles.

If reserve exists, Plan may still evaluate against reserve alone and must explain
that checkpoint assessment is unavailable.

If checkpoint policy exists but no reserve exists and reset time is unavailable,
CodexBar must distinguish "policy exists but cannot currently be evaluated" from
`NO_PLAN`.

Partial capability is preferable to collapsing all Plan information into one
generic unknown state.

## 9. Checkpoint validity

Within one `UsageWindowId` policy:

- checkpoint times must be unique;
- order of entry has no semantic meaning;
- policy is normalized to a deterministic ordering;
- `minimum_remaining` uses existing bounded Fraction semantics;
- time-to-reset uses a non-negative finite duration representation.

Non-monotonic checkpoint floors are allowed.

For example, this is structurally valid:

- 72 h -> 40%;
- 24 h -> 50%.

Plan evaluates compliance with explicit user policy. It does not decide whether the
policy is operationally feasible or likely to be achieved.

A UI may warn about unusual policy shapes, but feasibility is not a validity rule.

## 10. Temporal representation

The canonical persisted/domain duration should use an exact non-floating-point
representation.

The v1.8 product decision selects non-negative integer seconds as the canonical
duration unit.

UI may display human-friendly hours/days without changing domain meaning.

No policy semantics depend on timezone except conversion of the factual
timezone-aware reset timestamp into current time-to-reset.

## 11. Freshness

Plan may render an assessment derived from the last known snapshot together with
that snapshot's freshness.

A stale snapshot must not be presented as fresh Current.

Stale data must not cause a new operational Plan transition notification or any
other side effect.

The presentation should preserve the distinction between:

- the mathematical comparison represented by the last known data; and
- whether that data is currently authoritative/fresh.

## 12. Plan notification

v1.8 may add one narrowly scoped factual notification behavior:

> notify on transition into `BELOW_PLAN`.

The notification is eligible only when:

- notifications are enabled;
- the source snapshot is Current, not stale;
- an effective Plan evaluation is available;
- the previous tracked Plan state was not `BELOW_PLAN`;
- the new Plan state is `BELOW_PLAN`.

Repeated `BELOW_PLAN -> BELOW_PLAN` observations are silent.

Leaving `BELOW_PLAN` rearms the transition tracker.

v1.8 does not introduce a generic notification-rule engine or user-defined
expression language.

## 13. Settings intent

Plan checkpoint policy is explicit user configuration and belongs with canonical
application settings rather than a new independent policy file.

Existing schema-v2 reserve semantics must remain unchanged.

Adding persistent checkpoint data is expected to require a new settings schema
version. Exact JSON field shape is deferred to the settings requirement, but the
migration contract is already constrained:

- valid schema-v2 settings must remain readable;
- existing values retain exactly their prior meaning;
- migrated in-memory settings have no checkpoints unless explicitly configured;
- reading an older valid schema must not rewrite the file automatically;
- the next explicit settings save may write the new canonical schema atomically;
- corrupt/unsupported settings continue to fail under established safety
  semantics.

## 14. UI intent

Plan belongs in the Current Details experience because it evaluates Current against
explicit policy.

The Plan surface should explain at least:

- current remaining;
- configured reserve, when present;
- active checkpoint and its time-to-reset threshold, when evaluable;
- checkpoint floor, when active;
- effective floor;
- signed margin;
- Plan status;
- capability/freshness limitations when relevant.

The user should be able to understand why a status was produced without consulting
History.

Exact layout, copy and configuration controls are deferred to the UI requirement.

## 15. Relationship to Budget and Control

Budget remains an independent capability with its existing reserve/headroom
semantics.

Plan must not alter:

- Budget status contracts;
- reserve meaning;
- reset-credit opportunity semantics;
- explicit/manual redeem behavior.

Implementation may either consume an existing Budget assessment or consume the same
canonical reserve policy directly, provided there remains exactly one source of
truth for reserve.

That composition choice belongs to architecture after requirements are frozen.

## 16. Reset credits

Reset credits do not participate in the Plan-status calculation.

Automatic redeem remains prohibited.

Runtime notification of reset-credit expiry/count changes is not a core v1.8 Plan
requirement. It may be reconsidered only as a separately evidence-gated factual
extension when supported capability evidence is sufficient.

## 17. Explicitly out of scope

v1.8 does not add:

- consumption forecasting;
- estimated time-to-exhaustion;
- probability of exhaustion;
- predicted checkpoint arrival state;
- consumption-rate estimation;
- History-derived Plan policy;
- Historical Context input to Plan;
- empirical-band prediction;
- interpolation between checkpoints;
- inferred policy from labels or window durations;
- fixed "5h" or "weekly" domain identities;
- automatic reset-credit redemption;
- automatic reserve modification;
- generic notification rules/DSL;
- Plan Event Store;
- Activity/session inference;
- Cycle Explorer;
- expanded History exploration;
- speculative tray/backend rewrite;
- unrelated persistence or runtime refactoring.

## 18. Success criterion

v1.8 succeeds when a user can explicitly configure operating checkpoints for a
dynamic usage window and CodexBar can explain, using Current plus explicit settings
only:

- which policy component is applicable now;
- what effective floor is in force;
- how far Current is above, at or below that floor;
- when checkpoint evaluation is unavailable;
- and, optionally, when Current factually transitions below the configured Plan.

The result must remain deterministic, explainable and independent of historical
prediction.
