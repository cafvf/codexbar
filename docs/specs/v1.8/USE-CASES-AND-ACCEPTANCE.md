# CodexBar v1.8 — Use cases and acceptance criteria

Status: frozen for implementation

Acceptance criteria are deliberately grouped by observable behavior. They are not intended to produce one test function per AC; the test matrix maps multiple ACs onto compact vector/harness families.

## UC-1801 — Configure checkpoint policy

The user opens Settings, chooses a currently reported usage window, adds/edits/removes checkpoint rows, optionally enables Plan breach notifications, then saves.

### Acceptance

- **AC-1801** — checkpoint policy is keyed by opaque `UsageWindowId`; labels are presentation only; editing policy never derives targets from current `remaining`.
- **AC-1802** — persisted checkpoint coordinates are non-negative whole seconds; duplicate coordinates for one window are rejected, while non-monotonic minimum floors are accepted.
- **AC-1803** — Save validates/persists/applies the complete candidate; Cancel changes neither persisted nor effective settings; Reset restores empty checkpoints and disabled Plan breach notifications.
- **AC-1804** — editing currently visible windows preserves configured reserves/checkpoints for currently absent windows and preserves every unrelated AppSettings field.

## UC-1802 — Evaluate Current against Plan

A CURRENT snapshot contains a window with explicit reserve/checkpoint policy.

### Acceptance

- **AC-1805** — factual checkpoint coordinate is exactly `resets_at - observed_at`; changing render/test wall clock without changing the snapshot cannot change the assessment.
- **AC-1806** — checkpoint selection is stepwise: exact threshold equality activates the checkpoint, between thresholds the most recently crossed checkpoint remains active, and no interpolation occurs.
- **AC-1807** — effective floor equals `max(reserve, active checkpoint minimum)` among factually available components.
- **AC-1808** — signed `margin = remaining - effective_floor` preserves exact Decimal semantics, and above/equal/below maps to `ABOVE`/`AT`/`BELOW`.

## UC-1803 — Evaluate incomplete/applicability states

Plan policy exists but checkpoint evaluation is absent, not yet active or not resolvable.

### Acceptance

- **AC-1809** — no reserve and no checkpoint policy reports Plan not configured with no effective floor/margin/compliance.
- **AC-1810** — configured checkpoints before the first applicable threshold report `NO_ACTIVE_CHECKPOINT`; reserve remains independently applicable if configured.
- **AC-1811** — missing or past/invalid reset reports distinct `RESET_MISSING`/`RESET_INVALID`, fabricates no active checkpoint, and may still expose a reserve-only display assessment.
- **AC-1812** — whenever no effective floor exists, margin/compliance are absent rather than fabricated as zero/on-plan.

## UC-1804 — Persist and inspect Plan settings

The user loads/saves Settings and inspects them through the CLI.

### Acceptance

- **AC-1813** — canonical schema 3 round-trips exact values using exact keys, Decimal strings for fractions and non-negative integer seconds for checkpoint time.
- **AC-1814** — schema 1 and schema 2 load with in-memory Plan defaults and no rewrite; the next explicit valid Save writes schema 3.
- **AC-1815** — malformed checkpoint shape, duplicate time, invalid duration/fraction or wrong bool type follows the existing typed settings-document failure/fallback policy.
- **AC-1816** — `codexbar settings show` renders Plan opt-in/checkpoints human-readably while retaining origin/source-schema output.
- **AC-1817** — partial GUI/domain updates preserve every unedited AppSettings field and policy.

## UC-1805 — Inspect Plan in Current Details

The user opens Current Details.

### Acceptance

- **AC-1818** — Plan is derived from the already captured account observation and performs no second source read.
- **AC-1819** — CURRENT windows render resolution, effective floor source, signed margin and compliance when applicable, including not-configured/no-active/reset-unavailable states.
- **AC-1820** — STALE Current does not display a fresh/current “On plan” or “Below plan” claim.
- **AC-1821** — existing Budget headroom and reset-recommendation semantics remain unchanged.

## UC-1806 — Receive a Plan breach notification

The user has enabled both notification gates and Current crosses into `BELOW`.

### Acceptance

- **AC-1822** — first eligible CURRENT assessment is a silent baseline; `ABOVE/AT -> BELOW` emits one event; repeated BELOW deduplicates; recovery to ABOVE/AT rearms a later breach.
- **AC-1823** — STALE snapshots emit nothing and do not advance Plan tracker state.
- **AC-1824** — disabling either notification gate suppresses delivery but tracker state continues to evolve, so re-enable does not replay a suppressed breach.
- **AC-1825** — notification delivery failure is isolated from Current/Plan processing.
- **AC-1826** — one snapshot containing multiple independently breaching windows can produce distinct per-window events.

## UC-1807 — Track checkpoint activation, policy edits and reset cycles

Plan tracker observes repeated CURRENT snapshots.

### Acceptance

- **AC-1827** — within one resolved policy/cycle, a transition from no active floor/compliance to an active checkpoint that is already BELOW may emit a breach.
- **AC-1828** — changing reserve/checkpoint policy establishes a new silent baseline; notification enable/disable flags are not part of policy identity.
- **AC-1829** — a new resolved `resets_at` with configured checkpoints establishes a new silent cycle baseline.
- **AC-1830** — configured checkpoints with missing/invalid reset are ineligible for Plan breach notification until checkpoint capability is factually resolvable again.

## UC-1808 — Adopt authoritative Current after redeem

A manual redeem completes and returns a fresh composed account observation.

### Acceptance

- **AC-1831** — post-redeem observation enters the same tray `adopt_snapshot()` Current/alert path, with no second Plan-specific source read or mutation.
- **AC-1832** — successful consume followed by any expected `UsageError` during refetch preserves terminal successful redeem evidence and fabricates no Current/Plan observation.

## UC-1809 — Preserve authority boundaries

The full v1.8 suite/regression harness executes.

### Acceptance

- **AC-1833** — Plan evaluation imports/uses no History or Historical Context authority.
- **AC-1834** — Budget outputs for existing vectors and LOW/EXHAUSTED alert vectors remain unchanged by checkpoint configuration.
- **AC-1835** — no Plan code can invoke automatic redeem or infer/reset policy from reset-credit inventory/ledger.
- **AC-1836** — Plan/domain policy introduces no fixed 5h/weekly semantics or semantic parsing of `UsageWindowId`.
- **AC-1837** — no forecast, time-to-exhaustion estimate or exhaustion probability exists in v1.8.
- **AC-1838** — single-instance, History, Context, native/Qt fallback, Settings compatibility and existing redeem regression families remain green.
