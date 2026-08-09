## REQ-SETTINGS-001 — target acceptance complete

Target workstation: Ubuntu/GNOME/Wayland.

The settings implementation completed both automated and physical validation.

Automated gate:
- `uv run pytest -ra` -> **129 passed** at the TASK-113 gate;
- `uv run ruff check src tests` -> passed;
- `uv run mypy` -> passed, no issues found;
- `uv run python -m compileall -q src` -> passed.

Physical validation:
1. Settings opened with the effective current values.
2. Save persisted LOW threshold, refresh interval and notification enablement.
3. Runtime-relevant values were applied without process restart.
4. Cancel left persisted/effective values unchanged.
5. Invalid threshold and refresh values kept the settings dialog open and did not partially persist.
6. Reset restored the documented defaults through the shared application use case.
7. Non-default valid settings survived process restart.
8. Final reset restored the documented defaults.
9. The active native Ayatana backend initially exposed no Settings action. This target-discovered
   integration defect was corrected by extending the helper UI-intent contract and adding Settings to
   the native menu; the target menu then exposed the expected settings surface.

During validation, refresh values above 3000 and near 3500 were observed to be accepted. This is correct:
the specified valid domain is inclusive `10..3600` seconds. Values above 3600, e.g. 3601, are invalid.

Disposition: **REQ-SETTINGS-001 validated and closed.**
