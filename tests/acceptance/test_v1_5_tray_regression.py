from pathlib import Path


def test_native_indicator_glance_contract_is_not_extended_with_reset_details() -> None:
    source = Path("src/codexbar/ui/tray.py").read_text()
    assert "reset_credits" not in source
    assert "redeem" not in source.lower()
