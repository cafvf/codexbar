from __future__ import annotations

import re
from pathlib import Path


def test_task_657_tray_glance_and_native_indicator_files_do_not_reference_context() -> None:
    for path in (
        Path("src/codexbar/ui/tray.py"),
        Path("src/codexbar/ui/native_indicator.py"),
    ):
        source = path.read_text(encoding="utf-8").lower()
        assert "historical context" not in source
        assert "contextpresenter" not in source


def test_task_658_history_lifecycle_files_do_not_depend_on_context_ui() -> None:
    for path in (
        Path("src/codexbar/ui/history_controller.py"),
        Path("src/codexbar/ui/history_dialog.py"),
        Path("src/codexbar/ui/history_tray.py"),
    ):
        source = path.read_text(encoding="utf-8")
        assert "HistoricalContextPanel" not in source
        assert "ContextPresenter" not in source


def test_task_659_context_ui_uses_only_descriptive_non_predictive_wording() -> None:
    source = "\n".join(
        Path(path).read_text(encoding="utf-8").lower()
        for path in (
            "src/codexbar/ui/context_panel.py",
            "src/codexbar/ui/context_viewmodel.py",
        )
    )

    forbidden_phrases = (
        "forecast",
        "predicted",
        "prediction",
        "probability",
        "confidence interval",
        "exhaustion risk",
    )
    assert not any(term in source for term in forbidden_phrases)

    # ETA is forbidden as a standalone predictive term, not as a substring of
    # ordinary words such as "retained" or "metadata".
    assert re.search(r"\beta\b", source) is None
