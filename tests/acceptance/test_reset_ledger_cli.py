from codexbar.__main__ import main
from codexbar.application.reset_ledger import ResetLedgerState
from codexbar.infrastructure.reset_event_sqlite import SqliteResetEventRepository


def test_absent_reset_ledger_inspection_is_non_destructive(tmp_path) -> None:
    path = tmp_path / "missing.sqlite3"

    inspection = SqliteResetEventRepository.inspect_path(path)

    assert inspection.state is ResetLedgerState.ABSENT
    assert inspection.event_count is None
    assert not path.exists()


def test_reset_ledger_inspect_cli_reports_absent_without_creating(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)

    exit_code = main(["reset-ledger", "inspect"])
    output = capsys.readouterr().out

    expected = tmp_path / ".local/share/codexbar/reset-ledger.sqlite3"
    assert exit_code == 0
    assert "State: absent" in output
    assert "Path:" in output
    assert not expected.exists()
