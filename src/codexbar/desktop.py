from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

APP_ID = "codexbar"
DESKTOP_FILENAME = f"{APP_ID}.desktop"
ICON_FILENAME = f"{APP_ID}.svg"
MANAGED_MARKER = "X-CodexBar-Managed=true"


class DesktopIntegrationError(RuntimeError):
    """Raised when a desktop integration operation cannot be completed safely."""


@dataclass(frozen=True, slots=True)
class DesktopPaths:
    launcher: Path
    application_entry: Path
    icon: Path
    autostart_entry: Path


@dataclass(frozen=True, slots=True)
class DesktopStatus:
    launcher_exists: bool
    application_installed: bool
    icon_installed: bool
    autostart_enabled: bool

    @property
    def installed(self) -> bool:
        return self.launcher_exists and self.application_installed and self.icon_installed


def _home(values: dict[str, str]) -> Path:
    return Path(values.get("HOME", str(Path.home()))).expanduser()


def _is_snap_scoped(path: Path, home: Path) -> bool:
    snap_root = home / "snap"
    try:
        path.resolve().relative_to(snap_root.resolve())
    except ValueError:
        return False
    return True


def _xdg_data_home(env: dict[str, str] | None = None) -> Path:
    values = dict(os.environ) if env is None else env
    home = _home(values)
    raw = values.get("XDG_DATA_HOME")
    if raw:
        candidate = Path(raw).expanduser()
        if not _is_snap_scoped(candidate, home):
            return candidate
    return home / ".local/share"


def _xdg_config_home(env: dict[str, str] | None = None) -> Path:
    values = dict(os.environ) if env is None else env
    home = _home(values)
    raw = values.get("XDG_CONFIG_HOME")
    if raw:
        candidate = Path(raw).expanduser()
        if not _is_snap_scoped(candidate, home):
            return candidate
    return home / ".config"


def resolve_launcher(explicit: str | Path | None = None) -> Path:
    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    argv0 = Path(sys.argv[0]).expanduser()
    if argv0.name == APP_ID and argv0.is_file():
        return argv0.resolve()
    found = shutil.which(APP_ID)
    if found is not None:
        return Path(found).resolve()
    raise DesktopIntegrationError(
        "installed 'codexbar' launcher not found; install with 'uv tool install' first"
    )


def desktop_paths(
    *,
    launcher: str | Path | None = None,
    env: dict[str, str] | None = None,
) -> DesktopPaths:
    data_home = _xdg_data_home(env)
    config_home = _xdg_config_home(env)
    return DesktopPaths(
        launcher=resolve_launcher(launcher),
        application_entry=data_home / "applications" / DESKTOP_FILENAME,
        icon=data_home / "icons" / "hicolor" / "scalable" / "apps" / ICON_FILENAME,
        autostart_entry=config_home / "autostart" / DESKTOP_FILENAME,
    )


def _desktop_exec(path: Path) -> str:
    value = str(path)
    if "\n" in value or "\r" in value:
        raise DesktopIntegrationError("launcher path contains a newline")
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("`", "\\`")
        .replace("$", "\\$")
    )
    return f'"{escaped}" --gui'


def _desktop_entry(launcher: Path, *, autostart: bool) -> str:
    lines = [
        "[Desktop Entry]",
        "Type=Application",
        "Version=1.0",
        "Name=CodexBar",
        "Comment=Show current Codex usage limits",
        f"Exec={_desktop_exec(launcher)}",
        "Icon=codexbar",
        "Terminal=false",
        "StartupNotify=false",
        "Categories=Utility;",
        MANAGED_MARKER,
    ]
    if autostart:
        lines.extend(["NoDisplay=true", "X-GNOME-Autostart-enabled=true"])
    return "\n".join(lines) + "\n"


def _icon_svg() -> str:
    return """<!-- CodexBar managed asset -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect x="5" y="5" width="54" height="54" rx="13" fill="#202123"/>
  <path d="M19 22 L31 32 L19 42" fill="none" stroke="#f2f2f2" stroke-width="5"
        stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M35 43 H48" fill="none" stroke="#f2f2f2" stroke-width="5" stroke-linecap="round"/>
</svg>
"""


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    tmp.write_text(content, encoding="utf-8")
    tmp.chmod(0o644)
    os.replace(tmp, path)


def _is_managed_desktop_file(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        return MANAGED_MARKER in path.read_text(encoding="utf-8")
    except OSError:
        return False


def install_desktop(
    *, launcher: str | Path | None = None, env: dict[str, str] | None = None
) -> DesktopPaths:
    paths = desktop_paths(launcher=launcher, env=env)
    if not paths.launcher.is_file():
        raise DesktopIntegrationError(f"launcher not found: {paths.launcher}")
    _atomic_write(paths.icon, _icon_svg())
    _atomic_write(paths.application_entry, _desktop_entry(paths.launcher, autostart=False))
    return paths


def enable_autostart(
    *, launcher: str | Path | None = None, env: dict[str, str] | None = None
) -> Path:
    paths = desktop_paths(launcher=launcher, env=env)
    if not paths.launcher.is_file():
        raise DesktopIntegrationError(f"launcher not found: {paths.launcher}")
    _atomic_write(paths.autostart_entry, _desktop_entry(paths.launcher, autostart=True))
    return paths.autostart_entry


def disable_autostart(
    *, launcher: str | Path | None = None, env: dict[str, str] | None = None
) -> bool:
    paths = desktop_paths(launcher=launcher, env=env)
    if not paths.autostart_entry.exists():
        return False
    if not _is_managed_desktop_file(paths.autostart_entry):
        raise DesktopIntegrationError(f"refusing to remove unmanaged file: {paths.autostart_entry}")
    paths.autostart_entry.unlink()
    return True


def uninstall_desktop(
    *, launcher: str | Path | None = None, env: dict[str, str] | None = None
) -> DesktopPaths:
    paths = desktop_paths(launcher=launcher, env=env)
    if paths.autostart_entry.exists():
        if not _is_managed_desktop_file(paths.autostart_entry):
            raise DesktopIntegrationError(
                f"refusing to remove unmanaged file: {paths.autostart_entry}"
            )
        paths.autostart_entry.unlink()
    if paths.application_entry.exists():
        if not _is_managed_desktop_file(paths.application_entry):
            raise DesktopIntegrationError(
                f"refusing to remove unmanaged file: {paths.application_entry}"
            )
        paths.application_entry.unlink()
    if paths.icon.exists():
        try:
            content = paths.icon.read_text(encoding="utf-8")
        except OSError as exc:
            raise DesktopIntegrationError(str(exc)) from exc
        if "CodexBar managed asset" not in content:
            raise DesktopIntegrationError(f"refusing to remove unmanaged file: {paths.icon}")
        paths.icon.unlink()
    return paths


def desktop_status(
    *, launcher: str | Path | None = None, env: dict[str, str] | None = None
) -> DesktopStatus:
    paths = desktop_paths(launcher=launcher, env=env)
    return DesktopStatus(
        launcher_exists=paths.launcher.is_file(),
        application_installed=_is_managed_desktop_file(paths.application_entry),
        icon_installed=(
            paths.icon.is_file()
            and "CodexBar managed asset" in paths.icon.read_text(encoding="utf-8")
        ),
        autostart_enabled=_is_managed_desktop_file(paths.autostart_entry),
    )
