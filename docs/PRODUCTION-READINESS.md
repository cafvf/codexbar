# CodexBar Production Readiness

Status: **Phases A and B applied; Phases C and D pending**

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

Pending. This phase must validate a fresh-user installation from public
documentation only, including install, first run, diagnostics, GUI/tray,
login/restart behavior, upgrade, and uninstall.

## Phase D — Maintenance Release

Pending. Only after Phase C closes should release metadata be advanced and a
maintenance release such as v1.8.1 be considered. Phase D should contain no new
functional scope unless a concrete defect discovered during Phase C requires a
fix.
