# Phase C — Context Runtime

Tasks: TASK-730..739

## Goal

Remove redundant Context work and unnecessary History object materialization
without changing v1.6 semantics.

## Tasks

- TASK-730: introduce explicit Current revision.
- TASK-731: introduce History runtime revision.
- TASK-732: test exact revision advancement/no-op rules.
- TASK-733: implement revision-aware Context cache.
- TASK-734: implement lean schema-v1 Context projection query.
- TASK-735: prove SQL contains no frozen Context selection/statistical semantics.
- TASK-736: run all v1.6 Context canonical/regression tests.
- TASK-737: characterize candidate SQL/cold Context/cache-hit timing.
- TASK-738: enforce cache-hit p95 <= 5 ms on target characterization.
- TASK-739: document before/after performance and semantic equivalence.

## Gate C

All v1.6 Context semantics pass; cache invalidation passes; lean query passes;
cache-hit budget passes; no schema migration; global gate green.
