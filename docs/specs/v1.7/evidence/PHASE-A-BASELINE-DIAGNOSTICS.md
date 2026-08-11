# CodexBar v1.7 Phase A — Baseline + Diagnostics Evidence

Status: Gate A green on target workstation; validated, not yet committed
Tasks: TASK-710..719
Frozen specification anchor: `b8c159987339546dff1caa19bdf1ff6107ae0fa7`
Validated inherited release: v1.6.0 (`774d7e4f077d935f05c5290325c16268c5e0652a`)

## Scope implemented

- bounded, in-memory runtime metrics with capacity 64 per operation;
- typed availability, freshness, operational-health and evidence-origin dimensions;
- `SystemHealthSnapshot` and DEC-1703 overall-health derivation;
- read-only local diagnostic adapters independent of Qt UI;
- `codexbar doctor` and `codexbar doctor --json`;
- diagnostics JSON schema version 1 and secret-minimization guards;
- target-workstation characterization tooling for app-server lifecycle and Phase A baselines;
- explicit Codex multi-bucket rate-limit selection with legacy fallback;
- explicit single-account local-history lineage limitation;
- source-contract, diagnostics, architecture and read-only regression tests.

No Phase B instance-ownership implementation is included. No persistent app-server
session is implemented.

## TASK-710 — pre-change global regression baseline

The pre-change baseline MUST be captured on the target checkout before the Phase A
root-ready package is extracted. The expected starting HEAD is the frozen
specification commit above.

Target-workstation evidence captured before applying Phase A:

- HEAD: `b8c159987339546dff1caa19bdf1ff6107ae0fa7`;
- pytest: `603 passed in 1.64s`;
- Ruff: `All checks passed!`;
- mypy: `Success: no issues found in 74 source files`;
- compileall: green;
- `git diff --check`: green;
- baseline command exit status: `0`.

The terminal capture remains the authoritative target-machine evidence.

## TASK-711..716 — diagnostics evidence

Automated Gate A coverage includes:

- capacity 64 and oldest-sample eviction at sample 65;
- `last` at N>=1, p50 only at N>=3, p95 only at N>=20;
- monotonic-duration measurement;
- canonical overall-health vectors;
- healthy Context infrastructure with insufficient coverage not degrading overall;
- read-only local Doctor inspection for absent and existing stores;
- malformed local History reported as component failure without repair;
- JSON schema version 1;
- raw email, bearer/JWT-like tokens, `sk-` tokens and secret assignments redacted;
- sensitive detail keys omitted.

Local-only Doctor performance is characterized separately from the optional external
source probe.

## TASK-717 — app-server characterization

`scripts/characterize_v17_phase_a.py` records at least 20 target-machine samples for:

- spawn;
- initialize;
- request;
- parse;
- shutdown;
- total one-shot lifecycle;
- full Current read.

The script deliberately uses the existing one-shot gateway lifecycle. Its phase
boundaries are characterization-only and do not introduce a persistent session.

Target workstation, Python 3.14.4, Linux 7.0.0-29-generic, N=20:

| Phase | p50 (ms) | p95 (ms) |
|---|---:|---:|
| spawn | 0.492 | 1.613 |
| initialize | 282.127 | 329.143 |
| request | 656.995 | 912.809 |
| parse | 0.180 | 0.235 |
| shutdown | 15.559 | 31.784 |
| total one-shot | 955.135 | 1235.441 |
| full Current read | 933.736 | 1222.721 |

The sum of the phase medians for spawn + initialize + shutdown is about 298 ms.
This is meaningful lifecycle overhead, but request latency remains the dominant
single phase and timing alone does not establish safe supervised reconnect/lifecycle
behavior.

## TASK-718 — source contract and lineage

Characterized fixtures cover:

- legacy-only `rateLimits`;
- explicit `rateLimitsByLimitId.codex`;
- explicit Codex plus unrelated buckets;
- malformed Codex bucket with valid legacy fallback;
- dynamic 720-minute window;
- malformed Codex data without fallback -> normalized schema failure.

Lineage remains `single_account_assumption` with `account_namespaced=false`. No
private `auth.json`, JWT claim, raw email, or undocumented account identifier is
used for durable History identity.

## TASK-719 — evidence-gated stop/go decisions

### Persistent app-server session

Decision for Phase A: **NO-GO for implementation; retain v1.6 one-shot behavior**.

The measurements show material lifecycle overhead (~298 ms from the sum of p50
spawn + initialize + shutdown phase medians), so a persistent session remains a
plausible future optimization. It is not authorized here because Phase A provides no
supervised lifecycle/reconnect design or failure-recovery evidence. Timing benefit
alone is insufficient under DEC-1719 / REQ-EVIDENCE-001.

### History prune cadence / SQLite WAL / Ayatana migration

Phase A decision: **NO-GO for implementation change; retain v1.6 behavior in this
phase**. These evidence gates are not closed by the Diagnostics work. Any later
proposal to change them still requires the dedicated characterization and physical
evidence required by the frozen v1.7 specification.

## Additional Phase A performance baselines

The characterization script also records:

- local-only Doctor;
- History 30-day read when History is readable;
- History 180-day read when History is readable;
- Context candidate read;
- cold Context computation;
- repeated v1.6 Context computation.

Target-workstation measurements, N=20:

| Path | p50 (ms) | p95 (ms) |
|---|---:|---:|
| Doctor local-only | 1.488 | 1.634 |
| History 30d read | 35.490 | 38.492 |
| History 180d read | 35.679 | 38.202 |
| Context candidate read | 12.162 | 14.502 |
| Context cold | 20.124 | 21.328 |
| repeated v1.6 Context behavior | 24.953 | 27.211 |

The local Doctor budget is therefore comfortably below the frozen 500 ms p95
threshold. The default Doctor source probe is external and was observed separately
(~886 ms for the displayed single run); it is not part of the local-only budget.

The inspected live History store contained 2,182 snapshots spanning only
2026-08-09 to 2026-08-11. Consequently, the 30d and 180d query timings above read
the same actually populated time span and must not be interpreted as a fully
populated 180-day retention stress fixture. The prior v1.6 full-retention
characterization remains the scale reference until a later dedicated fixture run.

## Gate A closure

Gate A is **GREEN on the target workstation**. Phase A is validated but is not yet
staged, committed, or pushed. Phase B remains blocked until the Phase A commit is
created and the pushed remote state is verified.

Final target-workstation evidence:

1. pre-change regression baseline: `603 passed in 1.64s`; Ruff green; mypy green in
   74 source files; compileall green; `git diff --check` green;
2. Phase A focused gate: `43 passed in 0.20s`;
3. evidence-origin regression after correction: `18 passed in 0.13s`;
4. Doctor text: overall `healthy`; environment and Qt fallback correctly report
   `fresh_read_only_probe`;
5. Doctor JSON: parsed successfully with exit status `0`;
6. Phase A characterization: N=20 recorded; local-only Doctor p95 `1.634 ms`;
7. characterization-script Ruff B023 finding corrected without changing timing
   boundaries; focused Ruff, mypy, and compileall checks green afterward;
8. final global gate: `630 passed in 1.65s`; Ruff `All checks passed!`; mypy
   `Success: no issues found in 77 source files`; compileall green;
   `git diff --check` green;
9. final scope review: 16 effective Phase A files (2 tracked modifications and 14
   new files), with no unexpected path reported by `git status --short`.

The implementation therefore satisfies the Phase A validation gate for TASK-710..719.
The persistent app-server decision remains NO-GO for implementation in this phase,
and no Phase B work is included.

Any contradiction with the frozen specification must be handled as a spec amendment,
not silently normalized here.
