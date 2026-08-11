# Phase D — Asynchronous Context UI

Tasks: TASK-740..749

## Goal

Move Context repository/summary work off the Qt interaction thread.

## Tasks

- TASK-740: implement framework-independent ContextController.
- TASK-741: implement worker submission and revision capture.
- TASK-742: implement obsolete-result rejection.
- TASK-743: integrate loading/ready/unavailable Context view states.
- TASK-744: remove synchronous full Context work from Qt render path.
- TASK-745: architecture-test forbidden synchronous repository path.
- TASK-746: test refresh/open/close races and late completion.
- TASK-747: measure synchronous Qt Context work and cold background latency.
- TASK-748: physical Open Details refresh/context responsiveness smoke.
- TASK-749: validate History/Current/Context lifecycle regressions.

## Gate D

No heavy Context work on Qt; obsolete results cannot render; target synchronous
Context UI work <= 50 ms p95; physical lifecycle green; global gate green.
