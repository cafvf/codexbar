from pathlib import Path


def test_reserve_configuration_is_independent_of_current_usage_value() -> None:
    source = Path("src/codexbar/ui/settings.py").read_text()

    assert "percent_left" not in source
    assert ".remaining" not in source
    assert "current_usage_windows" in source
    assert "_reserve_entry" in source
