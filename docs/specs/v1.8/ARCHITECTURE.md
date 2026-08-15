# CodexBar v1.8 — Plan architecture

Status: frozen for implementation

## 1. Target topology

```text
                         Codex account read
                                |
                    existing serialized account lane
                                |
                     authoritative UsageSnapshot
                                |
              +-----------------+------------------+
              |                 |                  |
         Usage alerts        Budget            Plan evaluate
              |                 |                  |
              |                 |        AppSettings policies
              |                 |        |                  |
              |                 |   usage_reserves   plan_checkpoints
              |                 |                  |
              |                 |                  v
              |                 |          WindowPlanAssessment
              |                 |             /          \
              |                 |       PlanPanel     PlanAlertService
              |                 |                        |
              +-----------------+------------------------+
                                        |
                              existing NotificationPort
```

History and Context are not on the Plan path.

## 2. New/extended type ownership

### Neutral domain quantities

Candidate new module:

```text
src/codexbar/domain/quantities.py
```

Owns:

- `TimeToReset`;
- `FractionDelta`.

Compatibility:

```text
domain.context imports TimeToReset from quantities
application.analytics imports FractionDelta from quantities
```

The imported symbols remain available under historical module paths so existing tests/callers need not migrate immediately.

Do not move `Fraction`.

### Settings-domain policy

Extend:

```text
src/codexbar/domain/settings.py
```

with:

```text
UsagePlanCheckpoint
    window_id: UsageWindowId
    time_to_reset: TimeToReset
    minimum_remaining: Fraction

UsagePlanCheckpointPolicy
    entries: tuple[UsagePlanCheckpoint, ...]
```

Policy invariants:

- unique `(window_id, time_to_reset)`;
- persisted checkpoint coordinates are exact whole seconds;
- immutable;
- canonical ordering;
- query by `UsageWindowId`;
- no monotonic-floor validation;
- no reserve field.

Extend `AppSettings`:

```text
usage_plan_checkpoints: UsagePlanCheckpointPolicy
plan_breach_notifications_enabled: bool
```

Defaults:

```text
empty checkpoints
false
```

Functional AppSettings updates preserve all other fields.

## 3. Pure Plan application module

Candidate:

```text
src/codexbar/application/plan.py
```

Owns:

```text
PlanCheckpointResolution
PlanCompliance
WindowPlanAssessment
evaluate_window_plan(...)
```

Suggested assessment fields:

```text
window_id: UsageWindowId
remaining: Fraction
reserve: Fraction | None
time_to_reset: TimeToReset | None
active_checkpoint: UsagePlanCheckpoint | None
checkpoint_resolution: PlanCheckpointResolution
effective_floor: Fraction | None
margin: FractionDelta | None
compliance: PlanCompliance | None
```

Evaluation input:

```text
UsageWindow
snapshot.observed_at
UsageReservePolicy
UsagePlanCheckpointPolicy
```

No `datetime.now()`/clock dependency.

No I/O.

No Qt.

No History/Context.

## 4. Evaluation algorithm

For one window:

```text
reserve = reserves.reserve_for(window.id)
checkpoints = checkpoint_policy.checkpoints_for(window.id)

if no checkpoints:
    resolution = NOT_CONFIGURED
    checkpoint_floor = None
else if window.resets_at is None:
    resolution = RESET_MISSING
    checkpoint_floor = None
else:
    try TimeToReset.from_instants(observed_at, resets_at)
    if negative:
        resolution = RESET_INVALID
        checkpoint_floor = None
    else:
        eligible = checkpoints where current_ttr <= checkpoint.time_to_reset
        if none:
            resolution = NO_ACTIVE_CHECKPOINT
            checkpoint_floor = None
        else:
            active = min(eligible, key=time_to_reset)
            resolution = ACTIVE
            checkpoint_floor = active.minimum_remaining

effective_floor =
    max(non-null reserve, non-null checkpoint_floor)
    or None

if effective_floor:
    margin = FractionDelta(remaining.value - effective_floor.value)
    compliance = ABOVE / AT / BELOW
else:
    margin = None
    compliance = None
```

## 5. Persistence adapter

Extend only:

```text
src/codexbar/infrastructure/settings.py
```

No new repository.

Schema 3 exact-key set extends schema 2.

`usage_plan_checkpoints` shape:

```json
{
  "<window-id>": [
    {
      "time_to_reset_seconds": 259200,
      "minimum_remaining": "0.55"
    }
  ]
}
```

Decode:

- key must be non-empty window ID string;
- list required;
- each row exact keys;
- seconds integer, bool rejected, `>=0`;
- fraction uses existing Decimal-string decoder;
- duplicate seconds for a window rejected through typed settings-document error.

Encode:

- window IDs sorted;
- checkpoints descending time-to-reset seconds;
- integer seconds;
- Decimal string.

No read-time rewrite.

## 6. Settings application and UI

Extend existing Settings dialog and actions.

Do not add another settings repository/use case.

The dialog maintains a draft checkpoint policy for current windows.

At candidate-save time:

1. load/preserve existing policies for windows not exposed by the current dialog;
2. replace only edited current-window policies;
3. immutably replace edited AppSettings fields;
4. Save through existing `SaveSettings`;
5. apply through existing `SettingsActions.apply`.

Checkpoint UI uses typed add/edit/remove controls.

Exact Qt widget composition is not normative.

## 7. CurrentAccountPresenter integration

`CurrentAccountPresenter` retains current `AppSettings` in addition to its existing Budget runtime.

`apply_settings(settings)`:

- updates stored settings;
- updates Budget runtime;
- makes the next render use new Plan policy.

`current()`:

- does not read the source;
- uses the already captured observation;
- withholds Plan windows from current presentation when usage is STALE;
- otherwise evaluates each usage window.

While touching this path, pass `self._settings.usage_policy()` into `UsageViewModel.from_snapshot()` to keep configured LOW semantics coherent with the tray.

No new presenter worker/controller.

## 8. PlanPanel

Candidate location:

```text
src/codexbar/ui/control_panel.py
```

or a cohesive extracted UI file if size/style constraints justify it.

The panel consumes `CurrentAccountViewState`.

It does not read Settings or infrastructure directly.

It renders per-window Plan information and explicit unavailable/not-configured states.

It does not compute checkpoint selection itself.

It does not calculate Budget headroom.

## 9. Plan alerts

Candidate module:

```text
src/codexbar/application/plan_alerts.py
```

Owns:

```text
PlanBreachEvent
PlanAlertTransitionTracker
PlanAlertService
plan_alert_message(...)
```

Uses existing `NotificationPort`.

The service retains current AppSettings or equivalent immutable policy reference and can receive live settings updates.

### Baseline state

Per window, keep only in memory:

```text
relevant_policy
resolved_cycle_key
previous_compliance
baseline_exists
```

`relevant_policy` consists only of:

- reserve for that window;
- checkpoint tuple for that window.

Notification flags are not part of policy identity.

Cycle key is used only when checkpoints are configured and reset is factually resolvable.

### Eligibility

Skip without state advance when:

- snapshot STALE;
- checkpoints are configured and reset is missing/invalid.

Otherwise evaluate.

### Rebaseline

Silent baseline on:

- first eligible observation;
- relevant policy change;
- resolved checkpoint cycle change.

Within the same resolved policy/cycle, `None -> BELOW` is a real transition when a checkpoint becomes active.

### Delivery

Tracker evaluation occurs regardless of notification gates.

Desktop delivery occurs only when both gates are true.

Delivery failure is isolated using the same notification error boundary as usage alerts.

## 10. Tray integration

Do not create a second polling loop.

Extend the existing `TrayController._state_from_snapshot()` path:

```text
snapshot
  -> existing usage AlertService
  -> PlanAlertService
  -> UsageViewModel
  -> TrayViewState
```

The same function is already used by:

- normal refresh completion;
- `adopt_snapshot()` after authoritative redeem refetch.

This preserves one integration path.

`TrayShell.apply_settings()` continues to update:

- UsagePolicy;
- global notifications;
- refresh interval;

and additionally updates PlanAlertService policy/opt-in.

## 11. Redeem coherence fix

`RedeemProcessManager._refetch_after_success()` catches expected `UsageError`, not only `UsageSourceError`.

Terminal redeem status remains success/already-success when refetch cannot produce Current.

No Plan evaluation occurs from an absent fabricated observation.

## 12. Adapter coherence fix

Normalize domain validation failure caused by duplicate normalized window IDs into `UsageSchemaError` at the app-server parsing boundary.

No ID-format change.

## 13. Dependency rules

Allowed:

```text
domain.settings -> domain.models / domain.quantities
application.plan -> domain.*
application.plan_alerts -> application.plan + notification port + domain.*
ui -> application/domain contracts
infrastructure.settings -> application settings port + domain settings
```

Prohibited:

```text
application.plan -> application.context/history/reset/redeem
application.plan_alerts -> reset consumer/redeem manager
application.budget -> application.plan
domain -> application/infrastructure/ui
```

## 14. No new runtime subsystems

v1.8 does not introduce:

- Plan database;
- Plan repository;
- Plan cache;
- Plan revision;
- Plan executor;
- Plan controller;
- Plan scheduler;
- Plan diagnostic subsystem.

System Health does not need a new “Plan subsystem” because Plan is a pure Settings+Current-derived capability, not an independently failing I/O subsystem.

Settings diagnostics may report schema 3 through existing settings health evidence.

## 15. Complexity stop rule

During implementation, if a proposed helper/abstraction:

- has only one trivial call site;
- does not protect a volatile boundary;
- does not remove demonstrated duplication;
- is not required by a REQ/AC/INV;

it should not be added.

The default implementation is the smallest typed change that keeps the existing harness green.
