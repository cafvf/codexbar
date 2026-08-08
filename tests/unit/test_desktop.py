from __future__ import annotations

from pathlib import Path

import pytest

from codexbar.desktop import (
    DesktopIntegrationError,
    disable_autostart,
    install_desktop,
    uninstall_desktop,
)


def _env(tmp_path: Path) -> dict[str, str]:
    return {
        "HOME": str(tmp_path),
        "XDG_DATA_HOME": str(tmp_path / "data"),
        "XDG_CONFIG_HOME": str(tmp_path / "config"),
    }


def _launcher(tmp_path: Path) -> Path:
    p = tmp_path / "bin" / "codexbar"
    p.parent.mkdir(parents=True)
    p.write_text("x", encoding="utf-8")
    return p


def test_uninstall_refuses_foreign_desktop_entry(tmp_path: Path) -> None:
    launcher = _launcher(tmp_path)
    env = _env(tmp_path)
    paths = install_desktop(launcher=launcher, env=env)
    paths.application_entry.write_text("[Desktop Entry]\nName=Foreign\n", encoding="utf-8")
    with pytest.raises(DesktopIntegrationError, match="unmanaged"):
        uninstall_desktop(launcher=launcher, env=env)


def test_disable_autostart_is_idempotent_when_absent(tmp_path: Path) -> None:
    launcher = _launcher(tmp_path)
    assert disable_autostart(launcher=launcher, env=_env(tmp_path)) is False


def test_install_script_uses_uv_tool_without_dev_extra() -> None:
    script = Path("scripts/install.sh").read_text(encoding="utf-8")
    assert "uv tool install" in script
    assert "PySide6" in script
    assert "--extra dev" not in script
    assert "desktop install" in script


def test_uninstall_script_removes_desktop_before_uv_tool() -> None:
    script = Path("scripts/uninstall.sh").read_text(encoding="utf-8")
    assert script.index("desktop uninstall") < script.index("uv tool uninstall codexbar")


def test_snap_scoped_xdg_paths_fall_back_to_canonical_home(tmp_path: Path) -> None:
    launcher = _launcher(tmp_path)
    home = tmp_path / "home"
    env = {
        "HOME": str(home),
        "XDG_DATA_HOME": str(home / "snap" / "code" / "255" / ".local" / "share"),
        "XDG_CONFIG_HOME": str(home / "snap" / "code" / "255" / ".config"),
    }

    paths = install_desktop(launcher=launcher, env=env)

    assert paths.application_entry == home / ".local/share/applications/codexbar.desktop"
    assert paths.icon == home / ".local/share/icons/hicolor/scalable/apps/codexbar.svg"
    assert paths.autostart_entry == home / ".config/autostart/codexbar.desktop"


def test_install_script_forces_canonical_user_local_uv_and_xdg_paths() -> None:
    script = Path("scripts/install.sh").read_text(encoding="utf-8")
    assert 'XDG_DATA_HOME="$HOME/.local/share"' in script
    assert 'XDG_CONFIG_HOME="$HOME/.config"' in script
    assert 'UV_TOOL_DIR="$HOME/.local/share/uv/tools"' in script
    assert 'UV_TOOL_BIN_DIR="$HOME/.local/bin"' in script
