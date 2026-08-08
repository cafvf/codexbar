from codexbar.__main__ import main


def test_cli_mock_smoke(capsys) -> None:
    assert main(["--mock"]) == 0
    output = capsys.readouterr().out
    assert "CodexBar" in output
    assert "Weekly: 81% left" in output
