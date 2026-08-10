from pathlib import Path


def test_monitor_and_policy_have_no_forecast_or_history_dependencies() -> None:
    source = Path("src/codexbar/application/reset_monitor.py").read_text().lower()

    forbidden = (
        "history",
        "slope",
        "forecast",
        "agent_count",
        "recent",
    )
    assert not any(term in source for term in forbidden)
