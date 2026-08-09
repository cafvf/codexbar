# v1.3 documentation coherence audit

Review baseline: `main` after target validation of REQ-HISTORY-001
Purpose: reconcile release/user/architecture documentation with the implemented and validated v1.3 behavior.

## Findings corrected

1. README and installation docs still presented 1.2.0 as the whole repository state even though `main`
   already contains validated v1.3 history behavior.
2. Product Spec still described v1.3 as planned and said the history ADR/schema decision had not yet been made.
3. v1.3 RELEASE gates remained mostly unchecked after automated and target validation.
4. ADR-007 described the physical schema as recommended rather than implemented and used transaction wording
   that did not name the actual Python `sqlite3.Connection` transaction scope.
5. Git workflow pre-commit/release commands omitted `scripts` even though scripts are part of the current
   Ruff/compileall gate.
6. No detailed `TRACEABILITY-REQ-HISTORY-001.md` existed alongside the established v1.1/v1.2 per-requirement
   traceability pattern.
7. User-facing docs did not document `history inspect`, `history clear`, retention, XDG data path, or the fact
   that history survives desktop/tool uninstall unless deliberately cleared/removed.
8. Changelog had no v1.3 release-candidate section.

## Important version distinction retained

The code behavior on `main` is a validated v1.3.0 release candidate, but package metadata still reports
1.2.0. Documentation now states this explicitly instead of prematurely claiming that v1.3.0 is already
tagged/released.

The metadata transition belongs to TASK-332 and should be atomic across:
- `pyproject.toml`;
- `src/codexbar/__init__.py`;
- `tests/unit/test_release_metadata.py`;
- `uv.lock`;
- final CHANGELOG/README/Product Spec release wording.

## Documents reviewed and intentionally unchanged

- `CONSTITUTION.md`: current rules remain consistent with the implementation and test/traceability approach.
- `docs/VALIDATION.md`: retained as a dated historical engineering-validation ledger; newer requirement-specific
  validation records provide current release evidence without rewriting historical failures/corrections.
- `docs/VALIDATION-REQ-HISTORY-001.md`: already matches observed target validation.
- v1.0-v1.2 requirement specifications/ADRs/validation records: historical release contracts remain unchanged.
- ADR-006 and earlier ADRs: no v1.3 change requires retroactive modification.

## Release conclusion

After applying this documentation package, the remaining release-close work is mechanical metadata/version
alignment, one final full gate, TASK-332 completion and annotated tag creation.

## Final release transition

The approved documentation set was promoted from validated-release-candidate wording to release 1.3.0
together with the project/package metadata transition. The generated `uv.lock` update remains the only
machine-generated metadata step and must be produced with `uv lock` before the final gate/tag.
