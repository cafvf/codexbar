import tomllib
from pathlib import Path


def test_project_version_is_1_5_0() -> None:
    payload = tomllib.loads(Path("pyproject.toml").read_text())
    assert payload["project"]["version"] == "1.5.0"


def test_release_documents_exist() -> None:
    for path in (
        Path("docs/specs/v1.5/RELEASE.md"),
        Path("docs/VALIDATION-v1.5.0.md"),
        Path("docs/RELEASE-CHECKLIST-v1.5.0.md"),
        Path("docs/TRACEABILITY-v1.5.md"),
    ):
        assert path.exists(), path
