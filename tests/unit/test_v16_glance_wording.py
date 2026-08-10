from pathlib import Path


def test_task_657_phase_e_does_not_change_frozen_glance_contract() -> None:
    source = Path("src/codexbar/ui/viewmodel.py").read_text(encoding="utf-8")

    assert 'f"{window.short_label}: {window.percent_left}%"' in source
    assert 'f"{window.short_label}: {window.percent_left}% left"' not in source
