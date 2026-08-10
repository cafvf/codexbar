from pathlib import Path


def test_validation_script_is_safe_by_default() -> None:
    source = Path("scripts/validate_v1_5.py").read_text()

    assert "--real-read" in source
    assert "--real-redeem" in source
    assert "destructive" in source.lower()
    assert "consume_reset_credit(" not in source
