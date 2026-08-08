# Implementation Review Against the Constitution

Date: 2026-08-08

## Current result
The project now has two vertical slices: REQ-USAGE-001 is implemented and target-validated, while
REQ-UI-001 is implemented through the Qt shell but still awaits target-desktop validation.

## Decisions retained

| Decision | Current form |
|---|---|
| Ports/adapters | `UsageProvider` isolates the Codex app-server adapter |
| Dynamic usage windows | no fixed five-hour/weekly fields in the domain |
| Typed boundaries | immutable dataclasses, normalized exceptions |
| Spec/TDD traceability | requirement -> AC -> test -> task -> code |
| Optional GUI dependency | core remains headless; PySide6 lives behind `gui` extra |

## REQ-UI-001 architecture

```text
QSystemTrayIcon / UsagePanel
          |
     TrayController  <---- Qt polls immutable state
          |
   ThreadPoolExecutor
          |
  RefreshCoordinator
          |
    GetCurrentUsage
          |
    UsageProvider
```

The key constraint is directional: the provider call never runs on the Qt GUI thread. `TrayController`
is framework-independent and owns the asynchronous transition `LOADING -> FRESH/STALE/ERROR`. Qt only
starts refreshes, polls completion, and renders state.

## Simplicity review
- No event bus was introduced.
- No plugin framework was introduced.
- No persistent cache was introduced; stale fallback remains process-local.
- No Qt types leak into domain/application code.
- No new background scheduler abstraction was added: one single-worker executor plus Qt timers is enough
  for the current requirement.
- Overlapping refresh calls are rejected rather than queued, preventing accidental request buildup.

## Error/input/output review
- Provider errors remain normalized below the UI boundary.
- `GuiDependencyError` makes missing PySide6 an explicit user-facing runtime error.
- `SystemTrayUnavailableError` distinguishes a missing desktop tray from a Codex/provider failure.
- `TraySettings` validates refresh and poll intervals before runtime.
- `TrayViewState` is the explicit presentation output with phases `LOADING`, `FRESH`, `STALE`, `ERROR`.

## Validation status
### Closed
- REQ-USAGE-001 automated tests.
- Real authenticated app-server interaction on the target Linux workstation, reported successful by the
  project owner.

### Open
- PySide6 smoke test in an environment with the GUI extra installed.
- Manual target-desktop validation of click/toggle, refresh responsiveness, tray availability and quit.
- Desktop installation/autostart requirement.

## Next specification slice
After REQ-UI-001 target validation, open REQ-DESKTOP-001 for installation, `.desktop` integration and
opt-in autostart. Historical storage, charts and richer notifications remain out of v1.0.


## UI correction and glanceable status — 2026-08-08
- Target Linux validation showed that registering a `QMenu` directly on `QSystemTrayIcon` can cause the shell to consume primary clicks. The shell now handles `Trigger` and `Context` explicitly and only pops the menu for the latter.
- Generic desktop imagery was replaced by a project-owned terminal-style icon; no OpenAI/ChatGPT/Codex logo is embedded.
- Presentation now carries a canonical `glance_text`, derived from normalized window duration identifiers. Known windows render as `5h` and `W`; absent windows are omitted.
- `QSystemTrayIcon` has no portable adjacent-text property. The Qt backend therefore exposes `glance_text` through its tooltip. A native Linux indicator-label backend remains an explicit capability task rather than an implicit Qt hack.

## Target-desktop tray activation correction
Target validation demonstrated that treating `QSystemTrayIcon.ActivationReason.Trigger` as a portable
Linux invariant was incorrect. On the tested desktop, removing the registered menu did not recover single
click; only double click reached the application and the reliable Quit route was lost. The shell therefore
uses an adaptive model: a registered menu is the guaranteed glance/control surface, while `Trigger` and
`DoubleClick` opportunistically open details. The details panel itself now exposes Quit. This is simpler
and safer than adding desktop-specific event hacks before REQ-UI-002/desktop-backend evaluation.
