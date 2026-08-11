from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from codexbar.application.instance_ownership import InstanceOwnershipError, InstanceOwnershipState

pytest.importorskip("PySide6")

ROOT = Path(__file__).resolve().parents[2]


def _subprocess_environment(tmp_path: Path) -> dict[str, str]:
    environment = os.environ.copy()
    existing = environment.get("PYTHONPATH")
    source = str(ROOT / "src")
    environment["PYTHONPATH"] = source if not existing else f"{source}{os.pathsep}{existing}"
    environment["QT_QPA_PLATFORM"] = "offscreen"
    environment["XDG_RUNTIME_DIR"] = str(tmp_path)
    return environment


def test_endpoint_identity_is_stable_per_user_session() -> None:
    from codexbar.ui.instance_ownership import instance_endpoint_name

    first = instance_endpoint_name({"WAYLAND_DISPLAY": "wayland-0"}, uid=1000)
    again = instance_endpoint_name({"WAYLAND_DISPLAY": "wayland-0"}, uid=1000)
    other = instance_endpoint_name({"WAYLAND_DISPLAY": "wayland-1"}, uid=1000)
    assert first == again
    assert first != other
    assert first.startswith("codexbar-1000-")


def test_guard_is_exclusive_and_released_without_stale_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from codexbar.ui.instance_ownership import _OwnershipGuard

    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    first = _OwnershipGuard("codexbar-test-guard")
    second = _OwnershipGuard("codexbar-test-guard")
    try:
        assert first.try_acquire()
        assert not second.try_acquire()
        first.close()
        assert second.try_acquire()
    finally:
        first.close()
        second.close()


def test_busy_guard_with_no_responsive_owner_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from codexbar.ui.instance_ownership import _OwnershipGuard, resolve_gui_instance

    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    endpoint = f"codexbar-test-{os.getpid()}-{time.monotonic_ns()}"
    guard = _OwnershipGuard(endpoint)
    assert guard.try_acquire()
    monkeypatch.setattr("codexbar.ui.instance_ownership._BUSY_OWNER_WAIT_MS", 60)
    monkeypatch.setattr("codexbar.ui.instance_ownership._BUSY_OWNER_RETRY_MS", 5)
    try:
        with pytest.raises(InstanceOwnershipError) as captured:
            resolve_gui_instance(endpoint_name=endpoint)
    finally:
        guard.close()
    assert captured.value.diagnostic.state is InstanceOwnershipState.AMBIGUOUS


def test_abrupt_server_exit_endpoint_is_recoverable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from codexbar.ui.instance_ownership import resolve_gui_instance

    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    endpoint = f"codexbar-stale-{os.getpid()}-{time.monotonic_ns()}"
    code = r"""
import os
import sys
from PySide6.QtCore import QCoreApplication
from PySide6.QtNetwork import QLocalServer

app = QCoreApplication([])
server = QLocalServer()
if not server.listen(sys.argv[1]):
    raise SystemExit(3)
print(server.fullServerName(), flush=True)
os._exit(0)
"""
    completed = subprocess.run(
        [sys.executable, "-c", code, endpoint],
        check=True,
        capture_output=True,
        text=True,
        env=_subprocess_environment(tmp_path),
    )
    assert completed.stdout.strip()

    resolution = resolve_gui_instance(endpoint_name=endpoint)
    assert resolution.is_owner
    assert resolution.owner is not None
    resolution.owner.close()


def test_competing_launches_produce_one_owner_and_one_secondary(
    tmp_path: Path,
) -> None:
    endpoint = f"codexbar-race-{os.getpid()}-{time.monotonic_ns()}"
    marker = tmp_path / "show-details.marker"
    code = r"""
import sys
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from codexbar.ui.instance_ownership import resolve_gui_instance

endpoint = sys.argv[1]
marker = Path(sys.argv[2])
resolution = resolve_gui_instance(endpoint_name=endpoint)
print(resolution.diagnostic.state.value, flush=True)
if resolution.is_owner:
    owner = resolution.owner
    assert owner is not None
    owner.bind_show_details(lambda: marker.write_text("shown\n"))
    app = QApplication.instance()
    assert isinstance(app, QApplication)
    QTimer.singleShot(900, app.quit)
    app.exec()
    owner.close()
"""
    environment = _subprocess_environment(tmp_path)
    first = subprocess.Popen(
        [sys.executable, "-c", code, endpoint, str(marker)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
    )
    second = subprocess.Popen(
        [sys.executable, "-c", code, endpoint, str(marker)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
    )
    first_out, first_err = first.communicate(timeout=5)
    second_out, second_err = second.communicate(timeout=5)
    assert first.returncode == 0, first_err
    assert second.returncode == 0, second_err
    states = sorted([first_out.strip(), second_out.strip()])
    assert states == ["owner", "secondary"]
    assert marker.read_text() == "shown\n"
