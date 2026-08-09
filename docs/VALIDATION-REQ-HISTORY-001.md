# REQ-HISTORY-001 — Target validation record

Status: validated
Target: Ubuntu / GNOME / Wayland
Release: v1.3
Date: 2026-08-08/09
Validated baseline: commit `314887d` or later

## Automated evidence

The complete repository gate passed before target validation:

```bash
uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
```

The automated suite covers:
- CURRENT capture and STALE/error exclusion;
- SQLite atomicity and persistence across repository instances;
- `[start, end)` query semantics;
- 30-day retention boundaries and cascade integrity;
- schema-v1 validation, corruption and unknown-schema fail-closed behavior;
- inspection and explicit clear;
- runtime failure isolation from tray/current usage and alerts;
- AC-HISTORY-037 history-clear runtime isolation;
- INV-HISTORY-001..008;
- v1.0-v1.2 regression guards.

## Controlled validation

Executed:

```bash
uv run python scripts/validate_history.py all
```

Observed:
- exact 30-day cutoff behaved as specified;
- observations strictly older than cutoff were deleted;
- observations exactly at cutoff were retained;
- child window rows remained referentially consistent;
- persisted data survived repository reopen;
- clear was idempotent and preserved schema v1;
- unsupported schema failed closed without replacement;
- corrupt storage failed closed without deletion/reset;
- controlled history append failure did not replace successful CURRENT usage.

Final controlled-validation result:

```text
PASS: all controlled history validation scenarios succeeded.
```

## Production-path persistence using temporary XDG data

Executed with a temporary `XDG_DATA_HOME`:

```bash
TMP_HISTORY="$(mktemp -d)"
export XDG_DATA_HOME="$TMP_HISTORY"

uv run codexbar history inspect
uv run codexbar --mock
uv run codexbar history inspect
uv run codexbar --mock
uv run codexbar history inspect
```

Observed:
- initial state was `absent`;
- `--mock` created schema-v1 history through the normal application composition;
- subsequent inspection reported readable persisted history;
- history remained available across separate CodexBar processes;
- repeated deterministic observations behaved idempotently when the logical observation identity matched.

Temporary environment was removed after validation.

## Production-path clear using temporary XDG data

Executed:

```bash
uv run codexbar history clear
uv run codexbar history inspect
```

Observed:
- clear completed successfully;
- history state became `ready_empty`;
- schema remained `1`;
- snapshot count became `0`;
- no database replacement was required.

## Normal user XDG path

Normal-path inspection resolved history to the canonical host-user application-data location:

```text
/home/christiano/.local/share/codexbar/history.sqlite3
```

Observed normal history states during validation included:
- `ready_non_empty`;
- `ready_empty` after intentional clear.

The path is outside Snap-scoped storage and matches the v1.3 XDG policy.

## GUI/runtime validation

Executed the normal tray path:

```bash
uv run codexbar --gui
```

Observed:
- tray started normally;
- refresh remained responsive;
- current usage continued to update;
- no history-specific GUI blocking or error path appeared;
- after successful CURRENT refresh, history was readable from another terminal with
  `uv run codexbar history inspect`.

This confirms that SQLite history I/O remains compatible with the existing asynchronous refresh path.

## AC/requirement disposition

Physical/target evidence supplements the automated AC coverage.

Confirmed on target:
- persistent local history survives process restart;
- canonical XDG storage is used;
- explicit clear preserves schema;
- controlled 30-day retention behaves correctly;
- corrupt/unsupported storage is not silently repaired;
- history failure remains secondary to current usage;
- normal tray operation remains responsive with history capture enabled.

## Final disposition

REQ-HISTORY-001 target validation is complete.

TASK-331 is complete.

The remaining v1.3 work is release-close TASK-332:
- final traceability;
- validation index/document updates;
- changelog/product/release documentation;
- version metadata bump to 1.3.0;
- final repository gate;
- release commit/tag preparation.
