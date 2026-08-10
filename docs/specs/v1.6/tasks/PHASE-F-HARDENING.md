# Phase F — Performance + Hardening

Tasks: TASK-660..669

## Goal
Validate the chosen schema-v1 180-day design under realistic scale and faults.

## Tasks
- TASK-660: run 180-day DB-size characterization.
- TASK-661: run context-query p50/p95 characterization.
- TASK-662: run existing History-query p50/p95 characterization.
- TASK-663: optimize schema-v1 indexes/query only if justified.
- TASK-664: corruption/read failure injection.
- TASK-665: unusual sampling-gap fixtures.
- TASK-666: timezone/DST-equivalent-instant fixtures.
- TASK-667: repeated high-frequency polling pseudoreplication regression.
- TASK-668: full v1.5 protected-baseline gate.
- TASK-669: record tolerance/coverage diagnostics for future recalibration.

## Gate F
Performance evidence recorded, no unexplained P0 regression, no schema-v2
migration unless separately reviewed with measured justification.
