from pathlib import Path


def test_settings_dialog_exposes_canonical_reserve_fields() -> None:
    source = Path("src/codexbar/ui/settings.py").read_text()
    assert "five_hour_reserve_input" in source
    assert "weekly_reserve_input" in source
    assert "usage_reserves=reserves" in source
