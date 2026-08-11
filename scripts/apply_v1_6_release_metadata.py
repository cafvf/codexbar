from __future__ import annotations

from pathlib import Path


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"{label}: expected exactly one occurrence in {path}, found {count}"
        )
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def prepend_once(path: Path, marker: str, block: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if block.strip() in text:
        return
    if marker not in text:
        raise RuntimeError(f"{label}: marker not found in {path}")
    path.write_text(text.replace(marker, block + "\n" + marker, 1), encoding="utf-8")


def main() -> int:
    pyproject = Path("pyproject.toml")
    readme = Path("README.md")
    product = Path("PRODUCT_SPEC.md")
    changelog = Path("CHANGELOG.md")

    replace_once(
        pyproject,
        'version = "1.5.0"',
        'version = "1.6.0"',
        "project version",
    )
    replace_once(
        readme,
        "Current release: **1.5.0 — Control**.",
        "Current release: **1.6.0 — Context**.",
        "README release",
    )
    replace_once(
        readme,
        "- bounded local usage history with 24h/7d/30d descriptive analysis;",
        (
            "- bounded 180-day local usage history with 24h/7d/30d "
            "descriptive analysis;\n"
            "- empirical Historical context at the current time-to-reset "
            "using independent prior cycles;"
        ),
        "README capabilities",
    )
    replace_once(
        readme,
        (
            "History stores only eligible CURRENT observations and provides "
            "read-only descriptive analysis over:"
        ),
        (
            "History retains eligible CURRENT observations for 180 days and "
            "provides read-only descriptive analysis over:"
        ),
        "README retention",
    )

    readme_context = """### Historical context

Open Details also exposes **Historical context** for a current usage window when
authoritative reset metadata and comparable retained cycles are available.

Context compares the current remaining fraction with at most one real retained
observation from each prior authoritative cycle at a similar time-to-reset. It
uses the exact tolerance `min(0.05*h*, 2 hours)` and adapts presentation to the
number of independent comparable cycles.

Context is descriptive only. It does not forecast exhaustion, estimate probability
of future usage, influence alerts, alter Control/Budget policy, or trigger redeem.
"""
    prepend_once(
        readme,
        "### History\n",
        readme_context,
        "README Context section",
    )

    replace_once(
        product,
        (
            "Status: v1.5.0 release candidate\n"
            "Current validated baseline: 1.4.0\n"
            "Release candidate: 1.5.0\n"
            "Theme: Control"
        ),
        (
            "Status: v1.6.0 release candidate\n"
            "Current validated baseline: 1.5.0\n"
            "Release candidate: 1.6.0\n"
            "Theme: Context"
        ),
        "PRODUCT_SPEC header",
    )

    product_block = """### v1.6 — Context
1. Usage History retention expands to 180 days while remaining schema v1
   and CURRENT-only.
2. Context is anchored on authoritative `resets_at - observed_at`
   time-to-reset.
3. Historical cycle identity is `(UsageWindowId, resets_at)`.
4. Each prior cycle contributes at most one nearest real retained observation;
   no interpolation is introduced.
5. Comparable-cycle tolerance is exactly `min(0.05*h*, 2 hours)`, inclusive.
6. Coverage is based on independent comparable cycles:
   0–2 Insufficient, 3–4 Sparse, 5–9 Limited, 10+ Established.
7. Empirical median/range/quartiles/rank adapt to coverage and preserve ties
   explicitly.
8. Historical context is a separate Open Details surface and does not enter the
   tray/native glance.
9. Context failure is isolated from Current usage.
10. Context has no authority over alerts, Control/Budget, notifications, or
    reset-credit redeem.
11. Schema v1 and current indexes are retained after 180-day performance
    characterization.
12. Real-account validation is read-only; missing runtime capability may be
    recorded as an explicit release SKIP.
"""
    prepend_once(
        product,
        "## Non-functional invariants\n",
        product_block,
        "PRODUCT_SPEC v1.6",
    )

    changelog_block = """## 1.6.0 — 2026-08-10

Release candidate **Context**.

### Added
- Historical context in Open Details using independent prior authoritative
  cycles at a matching time-to-reset;
- exact hybrid comparison tolerance `min(0.05*h*, 2 hours)`;
- coverage-adaptive empirical range/median/quartile/rank presentation;
- explicit insufficient/unavailable Context states with history-failure
  isolation;
- v1.6 target validation, physical smoke, traceability and release tooling.

### Changed
- usage-history retention expands from 30 to 180 days while retaining history
  schema v1;
- cross-version Current/History/Control/Context composition was hardened and
  simplified;
- project version advances to 1.6.0.

### Compatibility and safety
- Context remains descriptive and non-predictive;
- Context does not influence alerts, Control/Budget, notifications or redeem;
- native tray glance remains usage-only;
- no History schema-v2 migration or speculative index is introduced.

### Validation
- Phase F target characterization: 17,280 snapshots / 34,560 window rows over
  180 days;
- history database fixture size: 7,868,416 bytes;
- schema v1 retained after query/performance characterization;
- fault, sampling-gap, timezone and pseudoreplication gates passed;
- final Phase G evidence is recorded in `docs/VALIDATION-v1.6.0.md`.
"""
    prepend_once(
        changelog,
        "## 1.5.0",
        changelog_block,
        "CHANGELOG v1.6",
    )

    print("Applied CodexBar v1.6 release metadata.")
    print("Next: uv lock")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
