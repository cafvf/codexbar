# CodexBar v1.7 — Test Plan

Status: frozen for implementation

## Test layers

1. Unit — diagnostic taxonomies, metrics, revisions, cache, state machines.
2. Repository integration — lean Context schema-v1 projection and History
   compatibility.
3. Application integration — health snapshot, Context async/cache, redeem async.
4. IPC integration — single-instance ownership and stale recovery.
5. Source-contract integration — legacy and multi-bucket payload fixtures.
6. Architecture — no forbidden Qt-thread I/O, private-auth lineage, or Context SQL
   semantic leakage.
7. CI acceptance — all declared Python minors.
8. Performance characterization — target workstation.
9. Physical GUI validation — Ubuntu/GNOME/Wayland.

## Mandatory unit families

### Health taxonomy

- healthy optional-unavailable-with-fallback;
- Context insufficient does not degrade;
- Current stale -> degraded;
- no Current + source failed -> needs attention;
- unsupported optional capability is factual, not failed.

### Runtime metrics

- capacity 64 exactly;
- oldest sample dropped at 65th;
- last at N=1;
- p50 hidden N=1..2;
- p50 visible N=3;
- p95 hidden N=1..19;
- p95 visible N=20;
- monotonic duration rejection/normalization as designed.

### Current/History revisions

- Current increments on accepted authoritative observation;
- STALE fallback does not pretend to be a new authoritative generation;
- History increments on real append;
- duplicate append no increment;
- prune 0 rows no increment;
- prune >0 rows increments;
- clear with rows increments.

### Context cache

- exact revision/window key;
- hit equality;
- Current invalidation;
- History invalidation;
- independent windows;
- stale async completion rejected.

### Redeem execution controller

- idle -> running -> terminal;
- duplicate start while running rejected;
- close suppresses UI adoption;
- process manager remains called once per accepted start;
- retry preserves attempt identity through process manager.

## Mandatory integration families

### Doctor

- text report healthy/degraded;
- JSON schema version 1;
- malformed local store becomes component diagnostic;
- no mutation;
- no raw account email/tokens.

### IPC

- owner starts;
- second instance sends SHOW_DETAILS;
- stale endpoint recovery;
- race for ownership produces one owner;
- owner shutdown cleans endpoint where possible.

### Context repository

- schema-v1 compatibility;
- lean query returns canonical ContextObservation fields;
- no unrelated History view model construction;
- current v1.6 statistical vectors remain unchanged.

### Source contract

Fixtures:

- legacy only;
- multi-bucket explicit codex;
- multi-bucket codex + unrelated limit;
- malformed codex bucket;
- dynamic non-300/non-10080 window durations.

### Budget

- no policy -> headroom None/not applicable;
- policy reserve zero remains a real explicit zero policy;
- above/at/below reserve unchanged.

### Native

- sustained stderr drain remains bounded;
- helper stdout command/event path remains live;
- dynamic label guide for arbitrary windows;
- fallback behavior.

## Architecture assertions

- Doctor does not import destructive consume implementation for execution.
- lineage code does not read auth.json/JWT/token files.
- Qt Context render does not call repository/full Context synchronously.
- Qt redeem action does not call external process manager synchronously on the
  event thread.
- Context SQL adapter does not implement tolerance/statistics.
- reset expiry monitor is not wired to new production notifications.
- `src` has no independent hard-coded release version literal.

## Performance characterization

Use dedicated scripts/tests, not normal shared-CI wall-clock assertions.

Record p50/p95 and sample count for:

- app-server spawn;
- initialization;
- request;
- parse;
- shutdown;
- full Current read;
- Context candidate SQL;
- cold Context;
- Context cache hit;
- synchronous Context UI work;
- IPC SHOW_DETAILS;
- local Doctor snapshot;
- History 30d/180d relevant reads.

## Physical validation

At release:

- one GUI instance;
- repeated launcher focuses existing Details;
- Open Details remains responsive while Context computes;
- delayed/mock or safe real redeem path does not freeze window;
- System Health lifecycle;
- native/fallback status;
- existing History/Settings/Context/Control lifecycle;
- no duplicate/stale widgets.
