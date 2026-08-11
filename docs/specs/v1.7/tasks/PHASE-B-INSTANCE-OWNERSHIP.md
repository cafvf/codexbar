# Phase B — Instance Ownership

Tasks: TASK-720..729

## Goal

Guarantee one GUI owner per user/session before adding further runtime concurrency.

## Tasks

- TASK-720: define typed local IPC protocol for PING/SHOW_DETAILS.
- TASK-721: implement QLocalServer owner.
- TASK-722: implement second-launch QLocalSocket client.
- TASK-723: resolve ownership before full GuiRuntime construction.
- TASK-724: implement stale-endpoint liveness detection/recovery.
- TASK-725: implement race-safe ownership tests with competing launches.
- TASK-726: bind SHOW_DETAILS to existing Open Details lifecycle.
- TASK-727: add diagnostic state for instance ownership.
- TASK-728: characterize local IPC round-trip p50/p95.
- TASK-729: physical second-launch/focus smoke.

## Gate B

One runtime owner, stale recovery and focus behavior pass automated tests; target
IPC p95 <= 250 ms; physical focus smoke green; global gate green.
