from pathlib import Path


def test_refresh_and_monitor_paths_do_not_invoke_redeem() -> None:
    paths = [
        Path("src/codexbar/application/refresh.py"),
        Path("src/codexbar/application/account_runtime.py"),
    ]
    for path in paths:
        source = path.read_text()
        assert "consume_reset_credit" not in source
        assert ".redeem(" not in source
