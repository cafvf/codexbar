from __future__ import annotations

import re
from pathlib import Path

RELEASE_VERSION = "1.7.0"


def test_v17_release_metadata_remains_recorded_as_historical_evidence() -> None:
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
    checklist = Path("docs/RELEASE-CHECKLIST-v1.7.0.md").read_text(encoding="utf-8")
    validation = Path("docs/VALIDATION-v1.7.0.md").read_text(encoding="utf-8")

    assert f"## {RELEASE_VERSION}" in changelog
    assert f"# CodexBar v{RELEASE_VERSION} — Release Checklist" in checklist
    assert f"project version: `{RELEASE_VERSION}`;" in validation


def test_runtime_version_has_no_independent_release_literal() -> None:
    source = Path("src/codexbar/__init__.py").read_text(encoding="utf-8")

    assert 'distribution_version("codexbar")' in source
    assert re.search(r'__version__\s*=\s*"\d+\.\d+\.\d+"', source) is None
