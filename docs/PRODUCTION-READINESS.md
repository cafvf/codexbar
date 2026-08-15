# CodexBar Production Readiness

Status: **Phases A, B, C and D complete**

Audited baseline: `c24639e811bd0507020e3fb6b4757f2849e6ae0c`
Validated product release: **v1.8.0 — Plan**

This record tracks productization work after the v1.8.0 feature release. It does
not define new product behavior, schema changes, forecasting, or a v1.9 feature
scope.

## Phase A — Repository Hygiene

- [x] `.omx/` local runtime/session state is excluded by `.gitignore`.
- [x] previously tracked `.omx/` content is removed from the Git index while
      preserving the developer's local working copy.
- [x] accidental empty `*:1:1` files identified in the production-readiness
      audit are removed.
- [x] `docs/GIT_WORKFLOW.md` explicitly names `.omx/` as non-versioned local
      state.
- [x] remote code search found no matches for the secret-like strings checked
      during the audit (`Authorization`, `Bearer`, `api_key`, `sk-`).
- [x] full Git history was scanned locally with Gitleaks: 77 commits and
      approximately 2.31 MB were inspected.
- [x] all eight Gitleaks findings were reviewed. They originate from the same
      initial commit and from `.omx/state/notify-fallback-delivery-v1/`.
- [x] the findings were classified as false positives for credentials: the
      detected high-entropy values are OMX delivery/ownership identifiers and
      hashes (`key_hash`, `owner_token`, `publisher_token`, thread/turn IDs),
      not service authentication credentials.
- [x] no credential rotation or Git-history rewrite is warranted by the
      evidence found.

The scan nevertheless confirmed the repository-hygiene decision: `.omx/`
contains local operational/session state and must remain untracked even though
the reviewed historical values are not service secrets.

## Phase B — Public Distribution Contract

- [x] the root README is the single canonical public installation authority.
- [x] `docs/INSTALLATION.md` no longer carries stale v1.3/schema-v1/30-day
      instructions and instead points to the canonical README procedure.
- [x] public installation is release-tag-oriented rather than implicitly
      `main`-oriented.
- [x] upgrade behavior is documented.
- [x] uninstall is documented as preserving persistent user data.
- [x] deliberate History deletion and safe full-data-purge guidance are
      documented without broad destructive commands.
- [x] `SECURITY.md` defines vulnerability-reporting, credential-boundary, local
      data, and repository-hygiene expectations.
- [x] the README links to the security policy.
- [x] feature development is described as frozen for productization; no v1.9
      feature scope is presented as committed.

## Phase C — Clean-room Validation

Complete.

- [x] clean-room checkout installed v1.8.0 through the documented installation
      path on Ubuntu/GNOME/Wayland.
- [x] upgrade from a real pre-1.0 installation preserved persisted Settings,
      History and reset-ledger state.
- [x] post-upgrade Doctor reported `Overall: healthy`; the Codex app-server
      source, Current read, Qt fallback and native-indicator diagnostic path
      remained available.
- [x] physical tray, Current, Open Details, History, Historical Context,
      Settings, System Health and Plan surfaces were exercised successfully.
- [x] a fresh CodexBar application state initialized from defaults without
      existing CodexBar persistence and created the expected History and
      reset-ledger stores.
- [x] the fresh-state test was isolated from the user's real persistence, and
      the original state was restored successfully afterward.
- [x] reinstall over v1.8.0 was idempotent and preserved persisted data.
- [x] uninstall removed the tool, launcher and managed desktop integration while
      preserving Settings, History and reset-ledger data.
- [x] final reinstall restored a healthy installation using the preserved data.
- [x] real session-login validation discovered a production defect: the
      graphical-session environment did not expose an NVM-installed `codex`
      executable through `PATH`, so the autostarted GUI could not reach the
      Codex app-server.
- [x] the defect was reproduced and characterized: the interactive Codex
      executable was under `~/.nvm/versions/node/.../bin/codex` and used
      `#!/usr/bin/env node`.
- [x] a regression fix added shell-independent user-local Codex discovery and
      confined PATH augmentation to the spawned app-server subprocess.
- [x] the regression fix passed 827 tests, Ruff, strict mypy, compileall and
      `git diff --check`.
- [x] repeated physical GNOME/Wayland login after installing the fix succeeded:
      the tray initialized normally and Current/Open Details accessed Codex
      without the previous executable-not-found error.

The login defect is the concrete maintenance reason for v1.8.1. No feature or
schema expansion resulted from Phase C.

## Phase D — Maintenance Release

Complete.

Phase C produced one concrete production defect, so v1.8.1 is justified as a
maintenance release. Its scope is restricted to:

- robust shell-independent discovery of a locally installed Codex executable
  for desktop/session launches;
- regression coverage for minimal graphical-session PATH environments;
- release metadata and production-readiness evidence.

No new product feature, persistence schema, forecasting behavior or subsystem is
in scope.

Release-candidate evidence:

- local release gate: 827 tests passed; Ruff, strict mypy, compileall and
  `git diff --check` passed;
- version authority reported 1.8.1 in uv-run, editable and isolated uv-tool
  modes;
- installed v1.8.1 Doctor reported `Overall: healthy`;
- physical GNOME/Wayland login validation passed with the Codex executable
  discovery fix;
- hosted CI run `31888631324` succeeded on exact commit
  `b449eec205c5a485b15c6f6ef335d3d330caabdb` for Python 3.12, 3.13 and 3.14
  plus isolated uv-tool version validation.
