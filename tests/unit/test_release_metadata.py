import tomllib
from importlib.metadata import version
from pathlib import Path

from codexbar import __version__


def test_package_version_matches_project_and_installed_metadata() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    expected = project["project"]["version"]

    assert version("codexbar") == expected
    assert __version__ == expected
