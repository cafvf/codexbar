# Phase A — Baseline + Diagnostics Domain

Tasks: TASK-710..719

## Goal

Establish measurable runtime evidence and the framework-independent Diagnose core
before optimization.

## Tasks

- TASK-710: capture v1.6 pre-change global regression baseline.
- TASK-711: implement bounded runtime metric domain/collector (capacity 64).
- TASK-712: implement diagnostic availability/health/evidence-origin types.
- TASK-713: implement `SystemHealthSnapshot` and overall derivation.
- TASK-714: implement local subsystem diagnostic adapters without Qt UI.
- TASK-715: implement `codexbar doctor` text renderer.
- TASK-716: implement `doctor --json`, schema version 1, secret-minimization tests.
- TASK-717: characterize app-server spawn/initialize/request/parse/shutdown.
- TASK-718: add upstream source-contract characterization:
  account lineage limitation + legacy/multi-bucket rate-limit fixtures.
- TASK-719: record Phase A baseline and evidence-gated stop/go decisions.

## Gate A

- Doctor unit/integration green;
- no-mutation/no-secret gates green;
- metric vector thresholds green;
- source fixtures characterized;
- app-server timing evidence recorded;
- global v1.6 regressions green.

Persistent app-server implementation is NOT part of Gate A.
