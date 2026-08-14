from __future__ import annotations

from codexbar.ui.native_indicator import (
    NATIVE_STDERR_MAX_LINES,
    BoundedDiagnosticBuffer,
    dynamic_label_guide,
)


def test_task_765_native_stderr_buffer_is_bounded_to_recent_lines() -> None:
    buffer = BoundedDiagnosticBuffer()
    for index in range(NATIVE_STDERR_MAX_LINES + 10):
        buffer.append(f"line-{index}")
    text = buffer.text()
    assert buffer.line_count() == NATIVE_STDERR_MAX_LINES
    assert "line-0" not in text
    assert f"line-{NATIVE_STDERR_MAX_LINES + 9}" in text


def test_task_766_native_guide_is_dynamic_and_preserves_longest_runtime_label() -> None:
    first = dynamic_label_guide("", "Alpha: 100%")
    second = dynamic_label_guide(first, "A: 1%")
    third = dynamic_label_guide(second, "Dynamic long window: 100% · stale")
    assert first == "Alpha: 100%"
    assert second == first
    assert third == "Dynamic long window: 100% · stale"
