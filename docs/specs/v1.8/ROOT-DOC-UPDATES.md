# CodexBar v1.8 — Root documentation update plan

Status: frozen update plan; Phase A applies sections 1–2 only

## 1. PRODUCT_SPEC.md

Current root metadata is stale after v1.7 release.

Target header concept:

```text
Current validated release: v1.7.0 — Diagnose
Active specification: v1.8 — Plan
```

Add v1.8 product evolution only after the v1.8 specification is frozen.

Do not rewrite historical v1.7 spec files merely because their implementation-time status says “frozen for implementation”.

## 2. docs/ROADMAP.md

Keep v1.8 Plan before v1.9 Explore.

Replace the older conceptual sketch:

```text
reserve_floor
checkpoints[]
notification_rules[]
```

with terminology consistent with released/current owners:

```text
existing usage_reserves
usage_plan_checkpoints
fixed factual Plan breach opt-in
```

Preserve the core boundary:

```text
Current + explicit Settings -> Plan
History/Context -X-> Plan
```

## 3. README.md

README must eventually document v1.8 user-visible Plan configuration/use.

However, the current checkout has an unstaged user-local README expansion.

Therefore:

- do not replace README from a generated root-ready artifact;
- do not restore/stash it;
- inspect its final local contents before v1.8 documentation integration;
- merge Plan documentation into that version deliberately;
- stage it only after user inspection.

## 4. Global TRACEABILITY / validation docs

After implementation:

- register REQ-PLAN-001..008;
- link v1.8 AC/test evidence;
- record physical target validation;
- preserve v1.7 release evidence unchanged.

## 5. Release metadata

`pyproject.toml` remains sole version authority.

Version bump occurs only in release-prep after all Plan behavior/evidence is green.
