from pathlib import Path


def test_control_shell_preserves_history_shell_lifecycle() -> None:
    source = Path("src/codexbar/ui/control_tray.py").read_text()
    assert "class ControlTrayShell(HistoricalTrayShell)" in source


def test_current_panel_composes_without_modifying_rich_usage_panel() -> None:
    source = Path("src/codexbar/ui/control_panel.py").read_text()
    assert "class CurrentAccountPanel(RichUsagePanel)" in source
