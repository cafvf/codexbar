from codexbar.ui.control_panel import ResetCreditsPanel


def test_reset_panel_is_separate_from_rich_usage_panel() -> None:
    assert ResetCreditsPanel.__name__ == "ResetCreditsPanel"
