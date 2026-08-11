from __future__ import annotations

import inspect

import codexbar.application.context as context_module
import codexbar.application.revisions as revisions_module
import codexbar.infrastructure.context_history as context_history_module
import codexbar.infrastructure.history_sqlite as history_sqlite_module
from codexbar.application.context import ContextCacheKey
from codexbar.application.revisions import CurrentRevision, HistoryRevision
from codexbar.domain.models import UsageWindowId


def _source(module) -> str:
    return inspect.getsource(module)


def test_task_730_731_revision_types_are_framework_independent() -> None:
    source = _source(revisions_module)

    assert "PySide6" not in source
    assert "sqlite3" not in source
    assert "codexbar.infrastructure" not in source


def test_task_733_cache_identity_contains_both_revisions_and_window() -> None:
    key = ContextCacheKey(
        current_revision=CurrentRevision(3),
        history_revision=HistoryRevision(5),
        window_id=UsageWindowId("dynamic"),
    )

    assert key.current_revision.value == 3
    assert key.history_revision.value == 5
    assert key.window_id.value == "dynamic"


def test_task_735_context_sql_adapter_contains_no_schema_migration_or_statistics() -> None:
    source = _source(context_history_module).upper()

    assert "CREATE TABLE" not in source
    assert "ALTER TABLE" not in source
    assert "QUANTILE" not in source
    assert "PERCENTILE" not in source
    assert "CONTEXTCOVERAGE" not in source
    assert "CONTEXTRANK" not in source


def test_context_selection_and_statistics_remain_in_application_domain_path() -> None:
    source = _source(context_module)

    assert "select_context_references" in source
    assert "summarize_context_reference_set" in source
    assert "query_candidates" in source


def test_phase_c_preserves_history_schema_v1_without_context_migration() -> None:
    assert history_sqlite_module._SCHEMA_VERSION == 1
    source = _source(context_history_module).upper()
    assert "SCHEMA_V2" not in source
    assert "CREATE TABLE" not in source
    assert "ALTER TABLE" not in source
