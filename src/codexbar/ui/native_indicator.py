from __future__ import annotations

import json
import os
import select
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final, Protocol, runtime_checkable

NATIVE_LABEL_GUIDE: Final = "5h: 100% · W: 100% · stale"
SYSTEM_PYTHON: Final = "/usr/bin/python3"


_UNSAFE_NATIVE_ENV_KEYS: Final = (
    "LD_LIBRARY_PATH",
    "PYTHONHOME",
    "PYTHONPATH",
    "GTK_PATH",
    "GIO_EXTRA_MODULES",
    "GIO_MODULE_DIR",
    "GI_TYPELIB_PATH",
)


def sanitized_native_environment(source: dict[str, str] | None = None) -> dict[str, str]:
    """Return an environment safe for launching distro-native GTK/Ayatana helpers."""

    env = dict(os.environ if source is None else source)
    for key in _UNSAFE_NATIVE_ENV_KEYS:
        env.pop(key, None)
    for key in tuple(env):
        if key == "SNAP" or key.startswith("SNAP_"):
            env.pop(key, None)
    env["PYTHONUNBUFFERED"] = "1"
    return env


@runtime_checkable
class NativeIndicator(Protocol):
    def show(self) -> None: ...

    def set_glance(self, text: str, *, stale: bool = False) -> None: ...

    def pump_events(self) -> None: ...

    def is_healthy(self) -> bool: ...

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class IndicatorDiagnosticStep:
    name: str
    ok: bool
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class IndicatorDiagnosticReport:
    steps: tuple[IndicatorDiagnosticStep, ...]
    exit_code: int
    stderr: str = ""

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and bool(self.steps) and all(step.ok for step in self.steps)


@dataclass(frozen=True, slots=True)
class NativeIndicatorAvailability:
    available: bool
    reason: str | None = None


def _helper_path() -> Path:
    return Path(__file__).with_name("native_indicator_helper.py")


def ayatana_availability(system_python: str = SYSTEM_PYTHON) -> NativeIndicatorAvailability:
    """Probe distro-provided PyGObject/Ayatana using system Python, not the uv environment."""

    if not Path(system_python).is_file():
        return NativeIndicatorAvailability(False, f"system Python not found: {system_python}")
    helper = _helper_path()
    if not helper.is_file():
        return NativeIndicatorAvailability(False, f"native indicator helper not found: {helper}")

    probe = (
        "import gi;"
        "gi.require_version('AyatanaAppIndicator3','0.1');"
        "gi.require_version('Gtk','3.0');"
        "from gi.repository import AyatanaAppIndicator3, Gtk"
    )
    try:
        completed = subprocess.run(
            [system_python, "-c", probe],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=3.0,
            check=False,
            env=sanitized_native_environment(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return NativeIndicatorAvailability(False, str(exc))
    if completed.returncode != 0:
        reason = completed.stderr.strip() or f"system probe exited {completed.returncode}"
        return NativeIndicatorAvailability(False, reason)
    return NativeIndicatorAvailability(True)


class AyatanaHelperIndicator:
    """Native indicator hosted in a distro-Python subprocess."""

    def __init__(
        self,
        *,
        icon_png: bytes,
        on_refresh: Callable[[], None],
        on_details: Callable[[], None],
        on_quit: Callable[[], None],
        on_settings: Callable[[], None] | None = None,
        system_python: str = SYSTEM_PYTHON,
    ) -> None:
        self._callbacks = {
            "refresh": on_refresh,
            "details": on_details,
            "quit": on_quit,
        }
        if on_settings is not None:
            self._callbacks["settings"] = on_settings

        self._tmpdir = TemporaryDirectory(prefix="codexbar-indicator-")
        icon_path = Path(self._tmpdir.name) / "codexbar.png"
        icon_path.write_bytes(icon_png)

        try:
            self._process = subprocess.Popen(
                [system_python, str(_helper_path()), "--icon", str(icon_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=sanitized_native_environment(),
            )
        except OSError:
            self._tmpdir.cleanup()
            raise

        try:
            self._await_ready(timeout_seconds=2.0)
        except Exception:
            self._terminate_process()
            self._tmpdir.cleanup()
            raise

    def show(self) -> None:
        return None

    def set_glance(self, text: str, *, stale: bool = False) -> None:
        rendered = f"{text} · stale" if stale else text
        self._send({"command": "set_glance", "text": rendered, "guide": NATIVE_LABEL_GUIDE})

    def pump_events(self) -> None:
        stdout = self._process.stdout
        if stdout is None:
            return
        while self._process.poll() is None:
            ready, _, _ = select.select([stdout], [], [], 0)
            if not ready:
                break
            line = stdout.readline()
            if not line:
                break
            try:
                event = json.loads(line).get("event")
            except json.JSONDecodeError:
                continue
            callback = self._callbacks.get(str(event))
            if callback is not None:
                callback()

    def is_healthy(self) -> bool:
        return self._process.poll() is None

    def close(self) -> None:
        if self._process.poll() is None:
            try:
                self._send({"command": "quit"})
                self._process.wait(timeout=1.0)
            except (BrokenPipeError, subprocess.TimeoutExpired):
                self._terminate_process()
        self._tmpdir.cleanup()

    def _await_ready(self, *, timeout_seconds: float) -> None:
        stdout = self._process.stdout
        if stdout is None:
            raise RuntimeError("native indicator helper has no stdout pipe")

        import time

        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                raise RuntimeError(self._startup_failure_message("helper exited before ready"))
            remaining = max(0.0, deadline - time.monotonic())
            ready, _, _ = select.select([stdout], [], [], min(0.05, remaining))
            if not ready:
                continue
            line = stdout.readline()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            if message.get("event") == "ready":
                return
            if "error" in message:
                detail = message.get("detail")
                text = str(message["error"])
                if detail:
                    text = f"{text}: {detail}"
                raise RuntimeError(text)
        raise RuntimeError(self._startup_failure_message("timed out waiting for helper readiness"))

    def _startup_failure_message(self, prefix: str) -> str:
        stderr = self._process.stderr
        detail = ""
        if stderr is not None and self._process.poll() is not None:
            try:
                detail = stderr.read().strip()
            except OSError:
                detail = ""
        return f"{prefix}: {detail}" if detail else prefix

    def _terminate_process(self) -> None:
        if self._process.poll() is not None:
            return
        self._process.terminate()
        try:
            self._process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=1.0)

    def _send(self, message: dict[str, str]) -> None:
        stdin = self._process.stdin
        if stdin is None or self._process.poll() is not None:
            return
        stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        stdin.flush()


def run_indicator_diagnostics(
    system_python: str = SYSTEM_PYTHON,
    *,
    timeout_seconds: float = 8.0,
) -> IndicatorDiagnosticReport:
    """Run the native helper in diagnostic mode and return structured step results."""

    helper = _helper_path()
    preflight: list[IndicatorDiagnosticStep] = []
    if not Path(system_python).is_file():
        preflight.append(
            IndicatorDiagnosticStep("system-python", False, f"not found: {system_python}")
        )
        return IndicatorDiagnosticReport(tuple(preflight), 2)
    preflight.append(IndicatorDiagnosticStep("system-python", True, system_python))
    if not helper.is_file():
        preflight.append(IndicatorDiagnosticStep("helper", False, f"not found: {helper}"))
        return IndicatorDiagnosticReport(tuple(preflight), 2)
    preflight.append(IndicatorDiagnosticStep("helper", True, str(helper)))

    try:
        completed = subprocess.run(
            [system_python, str(helper), "--diagnose"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
            env=sanitized_native_environment(),
        )
    except subprocess.TimeoutExpired as exc:
        return IndicatorDiagnosticReport(
            tuple(preflight + [IndicatorDiagnosticStep("helper-diagnostic", False, "timeout")]),
            124,
            str(exc),
        )
    except OSError as exc:
        return IndicatorDiagnosticReport(
            tuple(preflight + [IndicatorDiagnosticStep("helper-diagnostic", False, str(exc))]),
            2,
            str(exc),
        )

    steps = list(preflight)
    for raw in completed.stdout.splitlines():
        try:
            message = json.loads(raw)
        except json.JSONDecodeError:
            steps.append(IndicatorDiagnosticStep("helper-output", False, f"invalid JSON: {raw}"))
            continue
        if message.get("type") != "diagnostic":
            continue
        steps.append(
            IndicatorDiagnosticStep(
                name=str(message.get("step", "unknown")),
                ok=bool(message.get("ok", False)),
                detail=str(message["detail"]) if message.get("detail") is not None else None,
            )
        )
    if not any(step.name == "glib-loop" for step in steps):
        steps.append(
            IndicatorDiagnosticStep("helper-diagnostic", False, "diagnostic did not complete")
        )
    return IndicatorDiagnosticReport(tuple(steps), completed.returncode, completed.stderr.strip())


def create_ayatana_indicator(
    *,
    icon_png: bytes,
    on_refresh: Callable[[], None],
    on_details: Callable[[], None],
    on_quit: Callable[[], None],
    on_settings: Callable[[], None] | None = None,
) -> NativeIndicator | None:
    if not ayatana_availability().available:
        return None
    try:
        return AyatanaHelperIndicator(
            icon_png=icon_png,
            on_refresh=on_refresh,
            on_details=on_details,
            on_quit=on_quit,
            on_settings=on_settings,
        )
    except (OSError, RuntimeError):
        return None
