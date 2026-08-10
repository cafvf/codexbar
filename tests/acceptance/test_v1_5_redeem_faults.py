from pathlib import Path


def test_production_ui_redeem_surface_remains_manual_only() -> None:
    ui_source = "\n".join(
        path.read_text()
        for path in Path("src/codexbar/ui").glob("*.py")
    ).lower()

    assert "redeemprocessmanager" in ui_source.replace("_", "")
    assert "qmessagebox.question" in ui_source
    assert "consume_reset_credit" not in ui_source
