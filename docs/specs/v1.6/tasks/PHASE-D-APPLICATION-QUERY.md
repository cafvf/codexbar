# Phase D — Context Query + Application

Tasks: TASK-640..649

## Goal
Compose Current state with 180-day history into a Context application result
without modifying the authoritative Current model.

## Tasks
- TASK-640: define history/context repository port for required candidate reads.
- TASK-641: implement schema-v1 query adapter.
- TASK-642: implement `HistoricalContextService`.
- TASK-643: map current observation to context coordinate.
- TASK-644: return explicit unavailable/insufficient/sufficient states.
- TASK-645: isolate repository corruption/read failures.
- TASK-646: ensure no second upstream current-account read is triggered by Context.
- TASK-647: preserve dynamic UsageWindowId behavior.
- TASK-648: integration tests across multiple cycles/windows.
- TASK-649: composition-root wiring behind application interfaces.

## Gate D
Current + History -> Context integration green; injected Context failures leave
Current/Control/redeem healthy.
