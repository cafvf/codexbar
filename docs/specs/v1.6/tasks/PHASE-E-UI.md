# Phase E — Historical Context UI

Tasks: TASK-650..659

## Goal
Add a clear separate Historical Context surface in Open Details.

## Tasks
- TASK-650: define `ContextViewState`.
- TASK-651: add `HistoricalContextPanel`.
- TASK-652: render unavailable/insufficient state.
- TASK-653: render Sparse observed range + coverage.
- TASK-654: render Limited median + range + rank.
- TASK-655: render Established median + Middle 50% + rank.
- TASK-656: render ties without false strict-order wording.
- TASK-657: keep tray/native glance unchanged.
- TASK-658: keep History lifecycle unchanged.
- TASK-659: wording audit: no forecast/confidence/predictive terminology.

## Gate E
UI acceptance + existing Current/History lifecycle tests green; physical smoke
demonstrates Context is understandable and visually distinct.
