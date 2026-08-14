from pathlib import Path


def _source(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_control_tray_retains_the_resolved_presenter_context_controller() -> None:
    source = _source("src/codexbar/ui/control_tray.py")
    resolve = (
        "context_controller = context_controller or "
        "presenter.runtime_context_controller"
    )
    ownership = "self._context_controller = context_controller"

    assert resolve in source
    assert ownership in source
    assert source.index(resolve) < source.index(ownership)


def test_run_tray_resolves_presenter_bound_context_before_shell_construction() -> None:
    source = _source("src/codexbar/ui/control_tray.py")
    resolve = (
        "context_controller = context_controller or "
        "presenter.runtime_context_controller"
    )
    run_tray_start = source.index("def run_tray(")
    run_tray_source = source[run_tray_start:]

    assert resolve in run_tray_source
    assert "context_controller=context_controller" in run_tray_source


def test_mock_context_fixture_is_intended_for_physical_validation() -> None:
    source = _source("src/codexbar/infrastructure/mock_context.py")

    assert "Deterministic Context fixture for physical UI validation" in source
    assert '"window_300m"' in source
    assert '"window_10080m"' in source
