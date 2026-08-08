from __future__ import annotations

from pathlib import Path

from codexbar.desktop import (
    desktop_status,
    disable_autostart,
    enable_autostart,
    install_desktop,
    uninstall_desktop,
)


def _launcher(tmp_path: Path) -> Path:
    path = tmp_path / "tool bin" / "codexbar"
    path.parent.mkdir(parents=True)
    path.write_text("#!/bin/sh\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def _env(tmp_path: Path) -> dict[str, str]:
    return {
        "HOME": str(tmp_path / "home"),
        "XDG_DATA_HOME": str(tmp_path / "data"),
        "XDG_CONFIG_HOME": str(tmp_path / "config"),
    }


def test_ac_desktop_001_install_is_user_local_and_checkout_independent(tmp_path: Path) -> None:
    launcher = _launcher(tmp_path)
    paths = install_desktop(launcher=launcher, env=_env(tmp_path))
    text = paths.application_entry.read_text(encoding="utf-8")
    assert str(launcher.resolve()) in text
    assert "--gui" in text
    assert str(Path.cwd()) not in text


def test_ac_desktop_002_install_creates_desktop_entry_and_project_icon(tmp_path: Path) -> None:
    launcher = _launcher(tmp_path)
    paths = install_desktop(launcher=launcher, env=_env(tmp_path))
    assert paths.application_entry.is_file()
    assert paths.icon.is_file()
    assert "Icon=codexbar" in paths.application_entry.read_text(encoding="utf-8")


def test_ac_desktop_003_install_is_idempotent(tmp_path: Path) -> None:
    launcher = _launcher(tmp_path)
    env = _env(tmp_path)
    first = install_desktop(launcher=launcher, env=env)
    before = first.application_entry.read_text(encoding="utf-8")
    second = install_desktop(launcher=launcher, env=env)
    assert second == first
    assert second.application_entry.read_text(encoding="utf-8") == before


def test_ac_desktop_004_autostart_is_opt_in_and_reversible(tmp_path: Path) -> None:
    launcher = _launcher(tmp_path)
    env = _env(tmp_path)
    install_desktop(launcher=launcher, env=env)
    assert not desktop_status(launcher=launcher, env=env).autostart_enabled
    enable_autostart(launcher=launcher, env=env)
    assert desktop_status(launcher=launcher, env=env).autostart_enabled
    assert disable_autostart(launcher=launcher, env=env)
    assert not desktop_status(launcher=launcher, env=env).autostart_enabled


def test_ac_desktop_005_uninstall_removes_only_codexbar_owned_artifacts(tmp_path: Path) -> None:
    launcher = _launcher(tmp_path)
    env = _env(tmp_path)
    paths = install_desktop(launcher=launcher, env=env)
    enable_autostart(launcher=launcher, env=env)
    unrelated = paths.application_entry.parent / "other.desktop"
    unrelated.write_text("[Desktop Entry]\nName=Other\n", encoding="utf-8")

    uninstall_desktop(launcher=launcher, env=env)

    assert not paths.application_entry.exists()
    assert not paths.icon.exists()
    assert not paths.autostart_entry.exists()
    assert unrelated.exists()


def test_ac_desktop_006_status_reports_installation_and_autostart(tmp_path: Path) -> None:
    launcher = _launcher(tmp_path)
    env = _env(tmp_path)
    install_desktop(launcher=launcher, env=env)
    state = desktop_status(launcher=launcher, env=env)
    assert state.installed
    assert not state.autostart_enabled


def test_ac_desktop_014_snap_scoped_xdg_is_not_used_for_installation(tmp_path: Path) -> None:
    launcher = _launcher(tmp_path)
    home = tmp_path / "home"
    env = {
        "HOME": str(home),
        "XDG_DATA_HOME": str(home / "snap" / "code" / "255" / ".local" / "share"),
        "XDG_CONFIG_HOME": str(home / "snap" / "code" / "255" / ".config"),
    }

    paths = install_desktop(launcher=launcher, env=env)

    assert paths.application_entry.is_relative_to(home / ".local/share")
    assert paths.autostart_entry.is_relative_to(home / ".config")
    assert not paths.application_entry.is_relative_to(home / "snap")
