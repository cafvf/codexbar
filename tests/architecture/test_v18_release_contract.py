from __future__ import annotations

import tomllib
from pathlib import Path

EXPECTED_VERSION = "1.8.1"


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _project_version() -> str:
    payload = tomllib.loads(_read("pyproject.toml"))
    return str(payload["project"]["version"])


def _locked_project_version() -> str:
    payload = tomllib.loads(_read("uv.lock"))
    packages = payload.get("package", [])
    for package in packages:
        if package.get("name") != "codexbar":
            continue
        source = package.get("source", {})
        if isinstance(source, dict) and source.get("editable") == ".":
            return str(package["version"])
    raise AssertionError("editable codexbar package not found in uv.lock")


def test_release_version_authority_and_lock_are_coherent() -> None:
    assert _project_version() == EXPECTED_VERSION
    assert _locked_project_version() == EXPECTED_VERSION


def test_v18_release_documents_are_present_and_identify_plan() -> None:
    required = (
        "docs/TRACEABILITY-v1.8.md",
        "docs/VALIDATION-v1.8.0.md",
        "docs/RELEASE-CHECKLIST-v1.8.0.md",
        "docs/specs/v1.8/TRACEABILITY.md",
    )
    for path in required:
        text = _read(path)
        assert "Plan" in text

    changelog = _read("CHANGELOG.md")
    assert changelog.startswith("# Changelog\n\n## 1.8.1")
    assert "## 1.8.0 — 2026-08-14" in changelog
    assert "Validated **Plan** release." in changelog


def test_v18_traceability_mentions_every_frozen_acceptance_and_invariant() -> None:
    traceability = _read("docs/specs/v1.8/TRACEABILITY.md")

    for number in range(1801, 1839):
        assert f"AC-{number}" in traceability
    for number in range(1, 8):
        assert f"INV-PLAN-{number:03d}" in traceability


def test_release_ci_uses_release_neutral_version_validator() -> None:
    workflow = _read(".github/workflows/ci.yml")

    assert "scripts/validate_release_version_modes.py" in workflow
    assert "scripts/validate_v17_version_modes.py" not in workflow
    for minor in ("3.12", "3.13", "3.14"):
        assert f'- "{minor}"' in workflow
