# CodexBar — Future maintenance tasks

Status: active backlog

This file records maintenance items that originated outside a frozen release
contract. Product roadmap ownership is tracked in `docs/ROADMAP.md`.

## FUTURE-001 — Evaluate Ayatana deprecation migration

**Observed warning:** `libayatana-appindicator is deprecated. Please use
libayatana-appindicator-glib in newly written code.`

**Goal:** evaluate the distro/API migration path from the currently validated
AyatanaAppIndicator3 helper to the recommended `libayatana-appindicator-glib`
stack without weakening the isolated system-Python helper boundary or Qt
fallback.

**Acceptance direction:**

- identify supported Ubuntu/Debian GI bindings/API;
- preserve dynamic label, menu intents, readiness handshake and runtime
  supervision;
- retain environment sanitization and Qt fallback;
- perform physical Ubuntu/GNOME/Wayland validation before removing the current
  backend.

**Roadmap:** v1.7 evidence/investigation candidate (`V17-EVID-04`).

Migration is not automatically committed to v1.7. Evidence may justify retaining
the current validated backend.

## FUTURE-002 — Classify/silence canberra GTK module warning

**Observed warning:** `Gtk-Message: Failed to load module "canberra-gtk-module"`.

**Goal:** determine whether this is purely cosmetic on supported targets or
whether optional GTK sound/event integration is expected. Do not create a hard
runtime dependency unless product behavior actually requires it.

**Acceptance direction:**

- verify no current CodexBar behavior depends on the module;
- document optional distro package guidance if useful;
- otherwise suppress/avoid the warning only if this can be done without masking
  meaningful GTK diagnostics.

**Roadmap:** v1.7 evidence/investigation candidate (`V17-EVID-05`).

No hard dependency is committed.
