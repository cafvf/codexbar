from pathlib import Path

from codexbar.infrastructure.app_server import resolve_codex_executable


def _make_executable(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def test_path_codex_has_priority(tmp_path: Path) -> None:
    path_codex = _make_executable(tmp_path / "path-bin/codex")
    _make_executable(tmp_path / ".nvm/versions/node/v24.18.0/bin/codex")

    resolved = resolve_codex_executable(
        env={"HOME": str(tmp_path), "PATH": str(path_codex.parent)}
    )

    assert resolved == str(path_codex)


def test_user_local_bin_is_used_without_shell_path(tmp_path: Path) -> None:
    codex = _make_executable(tmp_path / ".local/bin/codex")

    resolved = resolve_codex_executable(
        env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}
    )

    assert resolved == str(codex)


def test_nvm_codex_is_found_with_minimal_desktop_path(tmp_path: Path) -> None:
    codex = _make_executable(
        tmp_path / ".nvm/versions/node/v24.18.0/bin/codex"
    )

    resolved = resolve_codex_executable(
        env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}
    )

    assert resolved == str(codex)


def test_highest_nvm_version_is_selected_deterministically(tmp_path: Path) -> None:
    _make_executable(tmp_path / ".nvm/versions/node/v22.20.0/bin/codex")
    newest = _make_executable(
        tmp_path / ".nvm/versions/node/v24.18.0/bin/codex"
    )
    _make_executable(tmp_path / ".nvm/versions/node/v9.99.0/bin/codex")

    resolved = resolve_codex_executable(
        env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}
    )

    assert resolved == str(newest)


def test_explicit_nvm_dir_is_honored(tmp_path: Path) -> None:
    nvm_dir = tmp_path / "custom-nvm"
    codex = _make_executable(nvm_dir / "versions/node/v24.18.0/bin/codex")

    resolved = resolve_codex_executable(
        env={
            "HOME": str(tmp_path),
            "NVM_DIR": str(nvm_dir),
            "PATH": "/usr/bin:/bin",
        }
    )

    assert resolved == str(codex)


def test_npm_global_is_fallback_when_nvm_is_absent(tmp_path: Path) -> None:
    codex = _make_executable(tmp_path / ".npm-global/bin/codex")

    resolved = resolve_codex_executable(
        env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}
    )

    assert resolved == str(codex)


def test_missing_codex_preserves_command_fallback(tmp_path: Path) -> None:
    resolved = resolve_codex_executable(
        env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}
    )

    assert resolved == "codex"


def test_transport_prepends_resolved_codex_bin_to_subprocess_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from unittest.mock import Mock

    from codexbar.infrastructure import app_server

    codex = _make_executable(
        tmp_path / ".nvm/versions/node/v24.18.0/bin/codex"
    )

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    monkeypatch.delenv("NVM_DIR", raising=False)

    process = Mock()
    process.stdin = Mock()
    process.stdout = Mock()
    process.stderr = Mock()
    process.poll.return_value = 0

    captured: dict[str, object] = {}

    def fake_popen(args, **kwargs):
        captured["args"] = args
        captured["env"] = kwargs["env"]
        return process

    monkeypatch.setattr(app_server.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(
        app_server.selectors,
        "DefaultSelector",
        lambda: Mock(),
    )

    app_server.SubprocessJsonRpcTransport()

    assert captured["args"] == [str(codex), "app-server", "--stdio"]
    subprocess_env = captured["env"]
    assert isinstance(subprocess_env, dict)
    assert subprocess_env["PATH"].split(":")[0] == str(codex.parent)
