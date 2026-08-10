from pathlib import Path


def test_settings_dialog_uses_current_reported_windows_not_fixed_ids() -> None:
    source = Path("src/codexbar/ui/settings.py").read_text()

    assert "current_usage_windows" in source
    assert 'UsageWindowId("window_300m")' not in source
    assert 'UsageWindowId("window_10080m")' not in source
    assert "No current usage windows available to configure." in source
