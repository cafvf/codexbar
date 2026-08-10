import tomllib
from pathlib import Path

from codexbar import __version__


def test_package_version_matches_project_metadata() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["version"] == __version__ == "1.5.0"
