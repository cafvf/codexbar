# Phase F — System Health UI + Selected Hardening

Tasks: TASK-760..769

## Goal

Expose live diagnostics in Open Details and close selected high-value ambiguities.

## Tasks

- TASK-760: implement SystemHealthViewState from shared diagnostic model.
- TASK-761: implement read-only System Health panel/surface.
- TASK-762: expose live runtime metrics/revisions/cache evidence where available.
- TASK-763: implement single-account lineage status wording.
- TASK-764: correct Budget no-policy headroom domain/UI semantics.
- TASK-765: implement bounded native-helper stderr drain/diagnostic buffer.
- TASK-766: make native width guide dynamic.
- TASK-767: explicitly classify/reset-monitor primitives as deferred, not active.
- TASK-768: incremental composition cleanup only where required.
- TASK-769: physical System Health/native/fallback/Open Details smoke.

## Gate F

Shared-model parity green; no diagnostic side effects; Budget wording correct;
native helper remains healthy/bounded; no reset notification activation; physical
UI green; global gate green.
