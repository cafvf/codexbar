from pathlib import Path


def test_no_production_ui_redeem_surface_exists_before_gate_d_passes() -> None:
    ui_source = "\n".join(
        path.read_text()
        for path in Path("src/codexbar/ui").glob("*.py")
    ).lower()

    assert "consume_reset_credit" not in ui_source
    assert "redeemprocessmanager" not in ui_source.replace("_", "")
