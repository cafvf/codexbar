from __future__ import annotations

import tomllib
from pathlib import Path

RELEASE_VERSION = "1.7.0"


def test_release_metadata_is_1_7_0() -> None:
    project = tomllib.loads(
        Path("pyproject.toml").read_text(encoding="utf-8")
    )
    lock = tomllib.loads(
        Path("uv.lock").read_text(encoding="utf-8")
    )

    assert project["project"]["version"] == RELEASE_VERSION

    codexbar_packages = [
        package
        for package in lock["package"]
        if package.get("name") == "codexbar"
    ]
    assert len(codexbar_packages) == 1
    assert codexbar_packages[0]["version"] == RELEASE_VERSION


def test_runtime_version_has_no_independent_release_literal() -> None:
    source = Path("src/codexbar/__init__.py").read_text(
        encoding="utf-8"
    )

    assert 'distribution_version("codexbar")' in source
    assert f'__version__ = "{RELEASE_VERSION}"' not in source
