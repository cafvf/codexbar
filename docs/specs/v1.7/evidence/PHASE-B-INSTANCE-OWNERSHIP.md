# CodexBar v1.7 Phase B — Instance Ownership Evidence

Status: Gate B green on target workstation; validated, not yet committed
Tasks: TASK-720..729
Phase A remote closure: `c3c46954aa59b8e398536c2fb4d891434a23c8a8`
Frozen specification anchor: `b8c159987339546dff1caa19bdf1ff6107ae0fa7`

## Scope implemented

- typed framework-independent `PING` / `SHOW_DETAILS` protocol;
- `QLocalServer` owner and `QLocalSocket` client;
- per-user/session deterministic endpoint identity;
- ownership resolution before `build_gui_runtime()`;
- advisory `flock` safety guard around ownership/stale-endpoint recovery;
- stale endpoint removal only while the acquisition guard is held;
- ambiguous ownership fails closed;
- `SHOW_DETAILS` binds to the existing `TrayShell.show_panel()` lifecycle;
- typed live instance-ownership diagnostic state;
- characterization tool for local `SHOW_DETAILS` p50/p95.

The advisory lock is not a remote-control channel. `QLocalServer` / `QLocalSocket`
remain the IPC contract. The lock exists only to serialize stale recovery and prevent
two competing launches from unlinking/reclaiming the endpoint concurrently. Kernel
release on process death provides race-safe crash recovery without manual lock-file
editing.

## TASK-720..727 — automated implementation evidence

The target workstation completed the focused Phase B validation successfully after
one implementation-only typing correction for PySide6 `QByteArray` conversion.

Validated behavior includes:

- typed `PING` / `SHOW_DETAILS` protocol;
- live-owner client detection;
- second-launch exit before full `GuiRuntime` construction;
- stale-endpoint recovery;
- race-safe ownership acquisition;
- fail-closed ambiguous ownership;
- existing Open Details lifecycle reuse;
- instance-ownership diagnostic state;
- architecture boundaries for early ownership resolution.

Focused Ruff, strict mypy, compileall and `git diff --check` were green after the
correction. No protocol or ownership semantics changed as part of the typing fix.

## TASK-728 — local IPC characterization

Target workstation characterization on 2026-08-11, N=20:

| Operation | N | p50 (ms) | p95 (ms) | min (ms) | max (ms) |
|---|---:|---:|---:|---:|---:|
| `SHOW_DETAILS` | 20 | 0.165 | 19.119 | 0.147 | 23.183 |

Endpoint observed during characterization:

`codexbar-1000-bc0d9bc2eb074716`

REQ-PERF-004 budget: **PASS**. The measured `SHOW_DETAILS` p95 of 19.119 ms is
well below the frozen 250 ms target-workstation budget.

A normal second `uv run python -m codexbar --gui` invocation while an owner was
running exited in approximately 0.316 seconds wall-clock while routing the request
to the existing owner instead of constructing another normal GUI runtime.

## TASK-729 — physical second-launch/focus smoke

Target Ubuntu/GNOME/Wayland physical validation passed:

1. the first CodexBar GUI owner started normally;
2. a second `--gui` invocation brought the existing Open Details window to the
   foreground and then exited;
3. no duplicate-runtime behavior was observed and the existing application remained
   operational;
4. after abnormal owner termination, a new launch recovered the stale local endpoint
   automatically without manual filesystem editing;
5. the recovered owner resumed normal application behavior.

This validates the user-visible second-launch/focus path and stale-endpoint recovery
required by the frozen Phase B gate. Automated ownership tests remain the primary
evidence for the at-most-one-owner invariant under competing launches.

## Gate B closure

Gate B is **GREEN on the target workstation**.

Final target-workstation evidence:

1. focused Phase B automated tests: green;
2. focused Ruff checks: green;
3. strict mypy: green after the `QByteArray` typing-only correction;
4. compileall: green;
5. `git diff --check`: green;
6. `SHOW_DETAILS` characterization: N=20, p50 0.165 ms, p95 19.119 ms;
7. REQ-PERF-004 (`p95 <= 250 ms`): PASS;
8. physical second-launch focus smoke: green;
9. abnormal-exit stale-endpoint recovery smoke: green;
10. final global gate (`pytest`, Ruff, strict mypy, compileall, `git diff --check`):
    reported green on the target workstation.

The Phase B implementation therefore satisfies TASK-720..729 and the frozen Gate B
validation requirements. Phase C remains blocked until this validated Phase B scope
is staged, committed, pushed, and remotely verified.

No Phase C Context-runtime implementation is included in this Phase B evidence.
