import tomllib
from pathlib import Path


def test_project_version_is_1_6_0() -> None:
    payload = tomllib.loads(Path("pyproject.toml").read_text())

    assert payload["project"]["version"] == "1.6.0"
