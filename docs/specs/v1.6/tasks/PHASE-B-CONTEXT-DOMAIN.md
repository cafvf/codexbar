# Phase B — Context Domain Core

Tasks: TASK-620..629

## Goal
Implement pure deterministic cycle/time/reference-set semantics.

## Tasks
- TASK-620: add `TimeToReset` value semantics using aware UTC instants.
- TASK-621: add authoritative `CycleIdentity(window_id, resets_at)`.
- TASK-622: define eligibility for missing/invalid reset metadata.
- TASK-623: implement grouping by independent cycle.
- TASK-624: exclude current cycle.
- TASK-625: implement hybrid tolerance `min(0.05*h*, 2h)`.
- TASK-626: implement nearest-real-observation selection.
- TASK-627: implement equal-distance later-observed-at tie break.
- TASK-628: guarantee one selected observation per cycle.
- TASK-629: freeze domain errors/absence states and architecture tests.

## Gate B
Run canonical TV-1601..1604 and TV-1608 plus architecture tests.
No SQLite/Qt dependency may enter pure domain selection logic.
