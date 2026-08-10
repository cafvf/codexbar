# Phase A — Retention + Characterization

Tasks: TASK-610..619

## Goal
Change the history retention contract to 180 days while preserving schema v1 and
measure realistic storage/query cost before any Context logic depends on it.

## Tasks
- TASK-610: locate/freeze current retention constant and cutoff semantics.
- TASK-611: change target retention to 180 days.
- TASK-612: add exact cutoff-boundary regression tests.
- TASK-613: preserve schema-v1 compatibility fixtures.
- TASK-614: build deterministic 180-day synthetic history fixture generator.
- TASK-615: measure rows/day and SQLite bytes/day.
- TASK-616: benchmark existing History queries on 180-day fixture.
- TASK-617: benchmark candidate window/cycle query shapes.
- TASK-618: add only necessary schema-v1 indexes if measurement justifies them.
- TASK-619: record characterization evidence and freeze persistence decision.

## Gate A
- retention tests green;
- schema remains 1;
- existing History acceptance suite green;
- characterization report exists;
- no schema migration introduced without measured failure.
