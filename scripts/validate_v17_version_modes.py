#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path

PACKAGE = "codexbar"
VERSION_PROBE = """
import json
from importlib.metadata import version
import codexbar

print(json.dumps({
    "runtime": codexbar.__version__,
    "metadata": version("codexbar"),
}))
""".strip()


@dataclass(frozen=True, slots=True)
class ModeResult:
    mode: str
    expected: str
    runtime: str
    metadata: str
    ok: bool
    detail: str = ""


def _project_version(root: Path) -> str:
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    return str(project["project"]["version"])


def _run(
    argv: list[str],
    *,
    root: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        argv,
        cwd=root,
        env=merged,
        text=True,
        capture_output=True,
        check=False,
    )


def _probe_mode(mode: str, argv: list[str], *, root: Path, expected: str) -> ModeResult:
    completed = _run(argv, root=root)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        return ModeResult(mode, expected, "", "", False, detail)

    try:
        payload = json.loads(completed.stdout.strip().splitlines()[-1])
        runtime = str(payload["runtime"])
        metadata = str(payload["metadata"])
    except (IndexError, KeyError, json.JSONDecodeError) as exc:
        return ModeResult(mode, expected, "", "", False, f"invalid probe output: {exc}")

    ok = runtime == metadata == expected
    detail = "" if ok else f"expected={expected!r} runtime={runtime!r} metadata={metadata!r}"
    return ModeResult(mode, expected, runtime, metadata, ok, detail)


def _tool_mode(root: Path, expected: str, python_request: str) -> ModeResult:
    with tempfile.TemporaryDirectory(prefix="codexbar-v17-tool-") as temporary:
        base = Path(temporary)
        tool_dir = base / "tools"
        bin_dir = base / "bin"
        env = {
            "UV_TOOL_DIR": str(tool_dir),
            "UV_TOOL_BIN_DIR": str(bin_dir),
        }

        installed = _run(
            [
                "uv",
                "tool",
                "install",
                "--force",
                "--python",
                python_request,
                ".",
            ],
            root=root,
            env=env,
        )
        if installed.returncode != 0:
            detail = installed.stderr.strip() or installed.stdout.strip()
            return ModeResult("uv-tool", expected, "", "", False, detail)

        listed = _run(["uv", "tool", "list", "--show-paths"], root=root, env=env)
        expected_header = f"{PACKAGE} v{expected}"
        if listed.returncode != 0 or expected_header not in listed.stdout:
            detail = listed.stderr.strip() or listed.stdout.strip()
            return ModeResult("uv-tool", expected, "", "", False, detail)

        executable = bin_dir / ("codexbar.exe" if os.name == "nt" else "codexbar")
        smoke = _run([str(executable), "--mock"], root=root, env=env)
        if smoke.returncode != 0 or "CodexBar" not in smoke.stdout:
            detail = smoke.stderr.strip() or smoke.stdout.strip()
            return ModeResult("uv-tool", expected, expected, expected, False, detail)

        return ModeResult("uv-tool", expected, expected, expected, True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate pyproject-backed CodexBar version derivation."
    )
    parser.add_argument(
        "--skip-tool",
        action="store_true",
        help="validate only project and editable modes",
    )
    parser.add_argument("--json-out", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = Path.cwd().resolve()
    expected = _project_version(root)
    python_request = f"{sys.version_info.major}.{sys.version_info.minor}"

    results = [
        _probe_mode(
            "uv-run",
            [
                "uv",
                "run",
                "--python",
                python_request,
                "python",
                "-c",
                VERSION_PROBE,
            ],
            root=root,
            expected=expected,
        ),
        _probe_mode(
            "editable",
            [
                "uv",
                "run",
                "--no-project",
                "--python",
                python_request,
                "--with-editable",
                ".",
                "python",
                "-c",
                VERSION_PROBE,
            ],
            root=root,
            expected=expected,
        ),
    ]

    if not args.skip_tool:
        results.append(_tool_mode(root, expected, python_request))

    payload = {
        "project_version": expected,
        "python": python_request,
        "results": [asdict(item) for item in results],
    }
    encoded = json.dumps(payload, indent=2, sort_keys=True)
    print(encoded)

    if args.json_out is not None:
        args.json_out.write_text(encoded + "\n", encoding="utf-8")

    return 0 if all(item.ok for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
