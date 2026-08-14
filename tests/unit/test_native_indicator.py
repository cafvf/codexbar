from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import Mock

import pytest

from codexbar.ui import native_indicator
from codexbar.ui.native_indicator import NativeIndicatorAvailability


def test_native_indicator_availability_is_explicit_value_object() -> None:
    unavailable = NativeIndicatorAvailability(False, "missing binding")
    assert unavailable.available is False
    assert unavailable.reason == "missing binding"


def test_native_label_guide_tracks_longest_runtime_label() -> None:
    first = native_indicator.dynamic_label_guide("", "5h: 100% · W: 100%")
    second = native_indicator.dynamic_label_guide(first, "5h: 1%")
    third = native_indicator.dynamic_label_guide(
        second,
        "Dynamic long quota window: 100% · stale",
    )

    assert first == "5h: 100% · W: 100%"
    assert second == first
    assert third == "Dynamic long quota window: 100% · stale"


def test_availability_uses_system_python_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "is_file", lambda self: True)
    completed = Mock(returncode=0, stderr="")
    run = Mock(return_value=completed)
    monkeypatch.setattr(native_indicator.subprocess, "run", run)

    result = native_indicator.ayatana_availability("/usr/bin/python3")

    assert result.available is True
    command = run.call_args.args[0]
    assert command[0] == "/usr/bin/python3"
    assert command[1] == "-c"
    assert "AyatanaAppIndicator3" in command[2]


def test_availability_reports_failed_system_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "is_file", lambda self: True)
    monkeypatch.setattr(
        native_indicator.subprocess,
        "run",
        Mock(return_value=Mock(returncode=1, stderr="No module named gi")),
    )

    result = native_indicator.ayatana_availability("/usr/bin/python3")

    assert result.available is False
    assert result.reason == "No module named gi"


def test_helper_indicator_sends_only_glance_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    stdin = io.StringIO()
    process = Mock(stdin=stdin, stdout=io.StringIO(), stderr=io.StringIO())
    process.poll.return_value = None
    monkeypatch.setattr(native_indicator.subprocess, "Popen", Mock(return_value=process))
    monkeypatch.setattr(
        native_indicator.AyatanaHelperIndicator, "_await_ready", lambda self, **_: None
    )

    indicator = native_indicator.AyatanaHelperIndicator(
        icon_png=b"png",
        on_refresh=lambda: None,
        on_details=lambda: None,
        on_quit=lambda: None,
    )
    indicator.set_glance("5h: 73% · W: 41%")

    import json

    payload_text = stdin.getvalue()
    payload = json.loads(payload_text)
    assert payload["command"] == "set_glance"
    assert payload["text"] == "5h: 73% · W: 41%"
    assert payload["guide"] == "5h: 73% · W: 41%"
    assert "token" not in payload_text.lower()
    assert "credential" not in payload_text.lower()

    process.poll.return_value = 0
    indicator.close()


def test_create_indicator_falls_back_when_system_bindings_are_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        native_indicator,
        "ayatana_availability",
        lambda: NativeIndicatorAvailability(False, "missing"),
    )

    result = native_indicator.create_ayatana_indicator(
        icon_png=b"png",
        on_refresh=lambda: None,
        on_details=lambda: None,
        on_quit=lambda: None,
    )

    assert result is None


def test_helper_readiness_accepts_ready_event() -> None:
    import tempfile

    with tempfile.TemporaryFile(mode="w+t") as stdout:
        stdout.write('{"event":"ready"}\n')
        stdout.seek(0)
        process = Mock(stdout=stdout, stderr=io.StringIO())
        process.poll.return_value = None

        indicator = native_indicator.AyatanaHelperIndicator.__new__(
            native_indicator.AyatanaHelperIndicator
        )
        indicator._process = process
        indicator._await_ready(timeout_seconds=0.2)


def test_helper_readiness_rejects_process_that_exits_before_ready() -> None:
    process = Mock(stdout=io.StringIO(), stderr=io.StringIO("registration failed"))
    process.poll.return_value = 1

    indicator = native_indicator.AyatanaHelperIndicator.__new__(
        native_indicator.AyatanaHelperIndicator
    )
    indicator._process = process

    with pytest.raises(RuntimeError, match="helper exited before ready: registration failed"):
        indicator._await_ready(timeout_seconds=0.2)


def test_create_indicator_falls_back_when_helper_startup_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        native_indicator,
        "ayatana_availability",
        lambda: NativeIndicatorAvailability(True),
    )
    monkeypatch.setattr(
        native_indicator,
        "AyatanaHelperIndicator",
        Mock(side_effect=RuntimeError("helper failed before ready")),
    )

    result = native_indicator.create_ayatana_indicator(
        icon_png=b"png",
        on_refresh=lambda: None,
        on_details=lambda: None,
        on_quit=lambda: None,
    )

    assert result is None


def test_indicator_diagnostics_parses_structured_helper_steps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "is_file", lambda self: True)
    stdout = "\n".join(
        [
            (
                '{"type":"diagnostic","step":"gi-import","ok":true,'
                '"detail":"/usr/lib/python3/dist-packages/gi/__init__.py"}'
            ),
            '{"type":"diagnostic","step":"ayatana-import","ok":true}',
            '{"type":"diagnostic","step":"glib-loop","ok":true,"detail":"completed"}',
        ]
    )
    monkeypatch.setattr(
        native_indicator.subprocess,
        "run",
        Mock(return_value=Mock(returncode=0, stdout=stdout, stderr="")),
    )

    report = native_indicator.run_indicator_diagnostics("/usr/bin/python3")

    assert report.ok is True
    assert [step.name for step in report.steps][-3:] == [
        "gi-import",
        "ayatana-import",
        "glib-loop",
    ]


def test_indicator_diagnostics_rejects_incomplete_helper_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "is_file", lambda self: True)
    monkeypatch.setattr(
        native_indicator.subprocess,
        "run",
        Mock(
            return_value=Mock(
                returncode=13,
                stdout=(
                    '{"type":"diagnostic","step":"indicator-create",'
                    '"ok":false,"detail":"boom"}\n'
                ),
                stderr="",
            )
        ),
    )

    report = native_indicator.run_indicator_diagnostics("/usr/bin/python3")

    assert report.ok is False
    assert any(step.name == "indicator-create" and not step.ok for step in report.steps)
    assert any(step.name == "helper-diagnostic" and not step.ok for step in report.steps)


def test_indicator_diagnostics_reports_missing_system_python(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "is_file", lambda self: False)

    report = native_indicator.run_indicator_diagnostics("/missing/python")

    assert report.ok is False
    assert report.steps[0].name == "system-python"
    assert report.steps[0].ok is False


def test_sanitized_native_environment_removes_external_runtime_overrides() -> None:
    source = {
        "HOME": "/home/tester",
        "DISPLAY": ":0",
        "WAYLAND_DISPLAY": "wayland-0",
        "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/1000/bus",
        "XDG_RUNTIME_DIR": "/run/user/1000",
        "XDG_CURRENT_DESKTOP": "ubuntu:GNOME",
        "LD_LIBRARY_PATH": "/snap/core20/current/lib/x86_64-linux-gnu",
        "PYTHONPATH": "/snap/code/current/usr/lib/python3",
        "GTK_PATH": "/snap/code/current/usr/lib/gtk-3.0",
        "GIO_EXTRA_MODULES": "/snap/code/current/usr/lib/gio/modules",
        "GI_TYPELIB_PATH": "/snap/code/current/usr/lib/girepository-1.0",
        "SNAP": "/snap/code/current",
        "SNAP_NAME": "code",
        "SNAP_REVISION": "123",
    }

    result = native_indicator.sanitized_native_environment(source)

    assert result["HOME"] == "/home/tester"
    assert result["DISPLAY"] == ":0"
    assert result["WAYLAND_DISPLAY"] == "wayland-0"
    assert result["DBUS_SESSION_BUS_ADDRESS"] == "unix:path=/run/user/1000/bus"
    assert result["XDG_RUNTIME_DIR"] == "/run/user/1000"
    assert result["XDG_CURRENT_DESKTOP"] == "ubuntu:GNOME"
    assert result["PYTHONUNBUFFERED"] == "1"
    assert "LD_LIBRARY_PATH" not in result
    assert "PYTHONPATH" not in result
    assert "GTK_PATH" not in result
    assert "GIO_EXTRA_MODULES" not in result
    assert "GI_TYPELIB_PATH" not in result
    assert not any(key == "SNAP" or key.startswith("SNAP_") for key in result)


def test_helper_indicator_launches_with_sanitized_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdin = io.StringIO()
    process = Mock(stdin=stdin, stdout=io.StringIO(), stderr=io.StringIO())
    process.poll.return_value = None
    popen = Mock(return_value=process)
    monkeypatch.setattr(native_indicator.subprocess, "Popen", popen)
    monkeypatch.setattr(
        native_indicator.AyatanaHelperIndicator, "_await_ready", lambda self, **_: None
    )
    monkeypatch.setenv("LD_LIBRARY_PATH", "/snap/core20/current/lib/x86_64-linux-gnu")
    monkeypatch.setenv("SNAP", "/snap/code/current")
    monkeypatch.setenv("DISPLAY", ":0")

    indicator = native_indicator.AyatanaHelperIndicator(
        icon_png=b"png",
        on_refresh=lambda: None,
        on_details=lambda: None,
        on_quit=lambda: None,
    )

    env = popen.call_args.kwargs["env"]
    assert env["DISPLAY"] == ":0"
    assert "LD_LIBRARY_PATH" not in env
    assert "SNAP" not in env
    process.poll.return_value = 0
    indicator.close()


def test_indicator_diagnostics_uses_sanitized_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "is_file", lambda self: True)
    run = Mock(
        return_value=Mock(
            returncode=0,
            stdout='{"type":"diagnostic","step":"glib-loop","ok":true}\n',
            stderr="",
        )
    )
    monkeypatch.setattr(native_indicator.subprocess, "run", run)
    monkeypatch.setenv("LD_LIBRARY_PATH", "/snap/core20/current/lib/x86_64-linux-gnu")
    monkeypatch.setenv("SNAP_NAME", "code")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")

    report = native_indicator.run_indicator_diagnostics("/usr/bin/python3")

    assert report.ok is True
    env = run.call_args.kwargs["env"]
    assert env["WAYLAND_DISPLAY"] == "wayland-0"
    assert "LD_LIBRARY_PATH" not in env
    assert "SNAP_NAME" not in env
