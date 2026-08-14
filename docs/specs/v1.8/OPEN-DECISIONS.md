# CodexBar v1.8 — Open Decisions

Status: no product-semantic decision blocks requirements drafting

The core product semantics are frozen in `PRODUCT.md` and `DECISIONS.md`.

The items below are intentionally deferred to the corresponding requirement or
architecture phase. Their resolution must preserve all frozen decisions.

## OD-1801 — Exact settings schema-v3 JSON shape

Constraint:

- schema evolution must be additive;
- existing `usage_reserves` keeps its current meaning;
- valid schema-v2 settings read compatibly;
- read alone does not rewrite the file.

Preferred default:

Add a dedicated per-window checkpoint-policy field rather than moving the existing
reserve into a new nested Plan object.

The exact field name and JSON nesting are deferred to the Settings REQ.

## OD-1802 — Internal Plan type and enum names

Product semantics define the states and values but do not require exact source-code
names.

Names should be chosen for clarity and strict typing after REQs are frozen.

## OD-1803 — Budget-to-Plan composition mechanism

Exactly one reserve source of truth is mandatory.

Architecture may choose whether Plan:

- consumes an existing `WindowBudget`/equivalent read model; or
- consumes the same canonical `UsageReservePolicy` directly.

The choice must not make Budget depend on Plan and must not duplicate reserve
configuration.

## OD-1804 — Exact Current Details layout and copy

Plan must be explainable and belong to Current Details.

Exact:

- section placement;
- labels;
- compact vs expanded presentation;
- formatting of durations/margins;
- configuration-control layout

are deferred to the UI REQ.

No choice may hide freshness/capability limitations or collapse "no policy" with
"policy unavailable".

## OD-1805 — Checkpoint configuration interaction design

The product requires explicit user editing of per-window checkpoints.

The exact interaction model is deferred to the UI/Settings REQs, including whether
editing uses:

- an extension of the existing Settings surface;
- a dedicated Plan subsection;
- row-based add/edit/remove controls.

No free-form DSL is planned.

## OD-1806 — Reset-credit expiry/count-change notifications

Default: deferred / no change.

Reconsider only with factual supported capability evidence.

If introduced, these notifications remain separate from Plan status and cannot
trigger automatic redeem.

## OD-1807 — Warning for non-monotonic checkpoint policy

Non-monotonic policies are valid and must not be rejected.

A non-blocking UI warning is optional.

Default: no special warning unless usability review demonstrates that one materially
improves understanding without implying invalidity.

## OD-1808 — Factual reset timestamp already in the past

Normal checkpoint evaluation assumes a non-negative factual time-to-reset.

The exact treatment of a fresh observation whose `resets_at` is unexpectedly
earlier than the evaluation clock is deferred to the Plan evaluation REQ.

Safety constraint:

- do not infer a new reset time;
- do not derive timing from History, labels or `UsageWindowId`;
- do not silently turn a negative duration into predictive information.

Preferred default for REQ review: treat checkpoint timing as unavailable/degraded
rather than fabricating a replacement reset time; reserve-only assessment may
remain available.
