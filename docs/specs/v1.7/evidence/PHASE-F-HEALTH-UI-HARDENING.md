# CodexBar v1.7 Phase F — System Health UI + Hardening Evidence

Status: **validated / complete**
Tasks: TASK-760..769
Base: Phase C commit `979a672718735af1c55f017729bda60b376ba65e`

## Final product shape

The final Phase F UX intentionally differs from the first implementation draft:

- **System Health is a separate tray-menu window**, not part of Open Details;
- **Historical Context belongs to Usage History**, not Open Details;
- Open Details remains focused on Current usage, Reset credits, Control/Budget and Redeem;
- System Health defaults to plain-language diagnostics;
- technical revisions/cache/runtime measurements are optional under `Show technical details`.

This layout was selected after physical usability validation showed that combining diagnostics and Historical Context with Open Details made the surface too large and difficult to interpret.

## Scope validated

Validated Phase F behavior includes:

- shared `SystemHealthViewState` derived from the read-only health snapshot;
- separate System Health tray action/window;
- understandable overall status and component names;
- live Current, History revision, Context revision/cache evidence and bounded runtime metrics;
- Context health auto-refresh while the System Health window is visible;
- idle/loading/ready/unavailable Context health semantics that do not falsely classify an unevaluated valid runtime as unavailable;
- explicit single-account History/Context lineage wording and account-switch hygiene;
- explicit note that automatic reset-count/reset-expiry monitoring is not enabled in v1.7;
- Budget no-policy headroom represented as not applicable and rendered as:
  - `Reserve policy: Not configured`
  - `Available above reserve: Not applicable`
  - `Status: No reserve policy`
- bounded native-helper stderr retention;
- native width guide based on runtime labels rather than fixed 5h/Weekly identities;
- reset-monitor primitives remain deferred/inactive;
- no reset fact notification ownership is added to GUI composition.

## Runtime-metric stabilization

Physical validation uncovered an important presentation defect: runtime metric introspection could leak a Python callable representation (`<built-in function ...>`) into System Health.

Incremental textual patches also produced invalid `p50_ms_ms` / `p95_ms_ms` accesses. Work was paused and a broader consistency audit was performed rather than continuing with micro-fixes.

The stabilization established one presentation boundary:

```text
RuntimeMetricSummary
        ↓
SystemHealthPresenter
        ↓
RuntimeMetricViewState
        ↓
SystemHealthViewState
        ↓
SystemHealthPanel
```

The Presenter owns interpretation/formatting of:

- `sample_count`;
- `last_ms`;
- `p50_ms`;
- `p95_ms`.

The Panel renders the presentation DTO and no longer introspects domain metric objects.

The same stabilization removed duplicate presentation of:

- `Reset monitoring`;
- runtime measurements.

## Static consistency audit

Before stabilization:

```text
HIGH=6
MEDIUM=142
LOW=383
RESULT: REVIEW REQUIRED
```

All six HIGH findings were manifestations of the same patch-drift family around duplicated `_ms` suffixes.

After stabilization:

```text
HIGH=0
MEDIUM=129
LOW=379
RESULT: NO HIGH-SEVERITY STATIC FINDINGS
```

The remaining MEDIUM/LOW findings are code-smell/debt indicators rather than release-blocking Phase-F defects. They include historical source-inspection tests, broad exception boundaries, long functions and similar heuristics.

## Automated validation

Final target-workstation global gate: **PASS**.

The stabilized worktree passed:

- `uv run ruff check src tests scripts --fix`;
- `uv run pytest -ra`;
- `uv run ruff check src tests scripts`;
- `uv run mypy`;
- `uv run python -m compileall -q src scripts`;
- `git diff --check`.

## Physical validation history

Earlier physical validation identified and drove correction of:

- System Health being too large inside Open Details;
- Historical Context being better located in Usage History;
- mock Context controller wiring;
- false `Historical Context — Unavailable` after History already displayed valid data;
- System Health language being too implementation-oriented;
- missing/unclear Reset monitoring note;
- missing runtime p50/p95 values;
- Python callable representations leaking into runtime metrics.

These were treated as validation failures, not accepted exceptions.

## Final physical smoke

Recorded: `2026-08-14T11:30:38-03:00`

Overall: **PASS**
Skipped checks: **0**

| Check | Result |
|---|---|
| System health opens as a separate tray-menu window and Open Details remains compact | PASS |
| Default view begins with understandable Overall status and plain-language component names | PASS |
| Account history scope explains single-local-account History/Context lineage and clear-history guidance after intentional account switch | PASS |
| Reset monitoring appears exactly once and clearly states the deferred automatic monitor is not enabled in v1.7 | PASS |
| Technical details are off by default and explain Revision, p50/median and p95 | PASS |
| Runtime measurements appears exactly once | PASS |
| Runtime measurements show real sample/last/p50/p95 data or an explicit insufficient-sample message | PASS |
| No Python implementation object or duplicated `p50_ms_ms`/`p95_ms_ms` field name is displayed | PASS |
| Historical Context health remains coherent with Usage History and is not falsely unavailable | PASS |
| Budget no-policy wording is physically observable and correct | PASS |

This final smoke supersedes the earlier failed readability/presentation smokes.

## Native/fallback hardening

The native Ayatana backend was physically observed working during D–F validation. Qt fallback remained covered by automated regressions where the native backend was active and therefore not directly observable in that physical session.

Native hardening includes:

- bounded stderr retention rather than unbounded accumulation;
- dynamic label-width guidance;
- preserved Qt fallback path.

## Validation conclusion

**Phase F complete.**

The final UI is physically understandable, System Health is read-only and separately scoped, Historical Context is located with History, runtime metrics are correctly typed/presented, no-policy Budget semantics are explicit, native hardening is retained, and the final stabilized checkout has no HIGH-severity static consistency findings.
