from __future__ import annotations

import ast
import tomllib
from pathlib import Path


def _runtime_module() -> ast.Module:
    source = Path("src/codexbar/__init__.py").read_text(encoding="utf-8")
    return ast.parse(source)


def test_runtime_version_is_derived_from_package_metadata() -> None:
    source = Path("src/codexbar/__init__.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    imports_metadata_version = any(
        isinstance(node, ast.ImportFrom)
        and node.module == "importlib.metadata"
        and any(alias.name == "version" for alias in node.names)
        for node in tree.body
    )

    assert imports_metadata_version
    assert 'distribution_version("codexbar")' in source


def test_runtime_module_has_no_independent_release_literal() -> None:
    tree = _runtime_module()

    release_assignments = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue

        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        value = node.value
        assigns_version = any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in targets
        )
        if (
            assigns_version
            and isinstance(value, ast.Constant)
            and isinstance(value.value, str)
            and value.value.count(".") == 2
            and all(part.isdigit() for part in value.value.split("."))
        ):
            release_assignments.append(value.value)

    assert release_assignments == []


def test_pyproject_remains_the_release_version_authority() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    version = project["project"]["version"]

    assert isinstance(version, str)
    assert version.count(".") == 2
    assert all(part.isdigit() for part in version.split("."))
