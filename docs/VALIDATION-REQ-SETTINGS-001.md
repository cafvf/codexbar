## REQ-SETTINGS-001 — automated implementation gate

Target workstation: Ubuntu/GNOME/Wayland.

The settings implementation passed the repository-wide automated gate after TASK-113:
- `uv run pytest -ra` -> **129 passed**;
- `uv run ruff check src tests` -> **passed**;
- `uv run mypy` -> **passed**, no issues in 25 source files;
- `uv run python -m compileall -q src` -> **passed**.

This closes TASK-114. REQ-SETTINGS-001 remains open because AC-SETTINGS-020..024 and the live runtime
effects still require physical target-desktop validation.

### TASK-115 — target GUI settings validation procedure

Use the development checkout with GUI dependencies available:

```bash
uv sync --extra dev --extra gui
uv run python -m codexbar --mock --gui
```

Validate the following sequence without editing `settings.json` manually.

1. **Open current settings**
   - Open the tray menu and choose `Settings`.
   - Confirm the dialog opens with LOW threshold `0.20`, refresh interval `60`, and notifications enabled
     when no persisted settings file exists.
   - Close with **Cancel**.
   - Confirm no settings file was created solely by opening/cancelling the dialog.

2. **Save and live runtime application**
   - Reopen `Settings`.
   - Set LOW threshold to `0.15`.
   - Set refresh interval to `10` seconds.
   - Disable notifications.
   - Choose **Save**.
   - Confirm the dialog closes without error.
   - Run `uv run python -m codexbar settings show` in another terminal and confirm:
     - `Origin: persisted`;
     - LOW threshold `15%`;
     - refresh interval `10 seconds`;
     - notifications disabled.
   - Keep the GUI process running for at least two automatic refresh periods and confirm it remains
     responsive. This validates live cadence application without restart.
   - Confirm manual Refresh still works and does not cause visible overlapping/frozen refresh behavior.

3. **Cancel semantics**
   - Open `Settings` again.
   - Change all three controls to visibly different values.
   - Choose **Cancel**.
   - Reopen the dialog and confirm the previously saved `0.15 / 10 / disabled` values remain.
   - Confirm `codexbar settings show` reports the same persisted values.

4. **Validation feedback**
   - Open `Settings`.
   - Enter an invalid LOW threshold such as `1.5` or a non-number.
   - Choose **Save**.
   - Confirm the dialog remains open and displays validation feedback.
   - Confirm `codexbar settings show` still reports the last valid persisted settings.
   - Repeat with refresh interval `9` and then `3601`; neither invalid value may be persisted.

5. **Reset semantics**
   - With valid custom values still persisted, open `Settings` and choose **Reset**.
   - Confirm the dialog remains usable and fields immediately return to `0.20 / 60 / enabled`.
   - Confirm `codexbar settings show` reports defaults after reset.
   - Confirm unrelated files in `~/.config/codexbar/` are unaffected if any exist.

6. **Restart persistence**
   - Save a non-default valid configuration again, for example `0.18 / 30 / disabled`.
   - Quit CodexBar cleanly.
   - Start it again with `uv run python -m codexbar --mock --gui`.
   - Reopen `Settings`.
   - Confirm the same non-default values are loaded after process restart.
   - Confirm `codexbar settings show` reports `Origin: persisted` with the same values.

7. **Final restoration**
   - Use the GUI Reset action or run:

```bash
uv run python -m codexbar settings reset
```

   - Confirm the final effective values are the documented defaults.

Record pass/fail observations for each numbered step before TASK-115 and REQ-SETTINGS-001 are closed.
