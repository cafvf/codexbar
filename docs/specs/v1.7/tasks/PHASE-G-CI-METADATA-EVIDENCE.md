# Phase G — CI + Metadata + Evidence Decisions

Tasks: TASK-770..779

## Goal

Move headless quality enforcement to GitHub and close all evidence-gated maintenance
decisions without forcing speculative changes.

## Tasks

- TASK-770: add GitHub Actions Python 3.12/3.13/3.14 matrix.
- TASK-771: run pytest/Ruff/mypy/compileall and suitable architecture gates.
- TASK-772: make pyproject metadata the single version authority.
- TASK-773: validate version under uv run/editable/uv tool modes.
- TASK-774: characterize History append/prune zero-effect frequency/cost.
- TASK-775: characterize concurrent Current write + History/Context reads; decide WAL.
- TASK-776: investigate Ayatana replacement path; prototype only if justified.
- TASK-777: classify canberra warning; no hard dependency by default.
- TASK-778: evaluate property-based testing; dependency optional.
- TASK-779: record explicit ADR/decision outcomes for app-server/prune/WAL/Ayatana.

## Gate G

Hosted matrix green; version drift structurally prevented; every evidence-gated
item has a written retain/change decision; any implementation change caused by
evidence has its own tests and physical validation where relevant; global gate
green.
