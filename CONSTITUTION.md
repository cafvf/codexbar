# CodexBar Engineering Constitution

Status: normative  
Version: 1.0

## C-01 — Specification precedes production behavior
Every externally observable behavior MUST trace to a requirement, use case, and acceptance criterion
before production implementation is considered complete.

## C-02 — Traceability is bidirectional
The normative chain is:

`REQ -> UC -> AC -> TEST -> TASK -> CODE`

A task does not invent behavior. A test without an acceptance criterion is allowed only for an
implementation invariant and MUST be labelled `INV-*`.

## C-03 — Tests derive from behavior, not coverage quotas
No minimum number of tests is a design goal. Tests cover distinct behaviors, boundary conditions,
contracts, regressions, and architectural invariants. Duplicate tests are removed.

## C-04 — Domain types carry meaning
No ambiguous primitive may cross a core boundary when a value object clarifies units or validity.
Fractions are `[0, 1]`; timestamps are timezone-aware; absence is represented explicitly and never
silently converted to zero.

## C-05 — Errors are normalized at boundaries
Expected infrastructure failures are translated to the CodexBar error taxonomy. Valid domain states
(e.g. an exhausted quota) are not exceptions. Unknown or malformed source data MUST NOT be converted
into fabricated usage.

## C-06 — Dependency direction
The domain imports no application, infrastructure, or UI modules. Application depends on domain
ports. Infrastructure implements ports. UI consumes application/view-state contracts and MUST NOT
parse Codex output.

## C-07 — External contracts are volatile
Codex CLI/web/app-server output is an external contract. Adapters MUST be isolated, contract-tested
against captured fixtures, and fail closed when the schema is unknown. Parsing terminal prose is a
fallback, not a domain assumption.

## C-08 — Simplicity before extensibility
An abstraction is introduced only when it serves a current requirement, protects a volatile boundary,
or removes demonstrated duplication. No plugin bus, event bus, generic repository, or framework-level
DI container is permitted in v1.0 without an ADR.

## C-09 — Releases have explicit scope
Each release specification defines goals, non-goals, acceptance gates, and tasks. New scope is moved
to a later release rather than silently added.

## C-10 — Quality gate
A release candidate MUST have: all scoped ACs passing; no orphan REQ/UC/AC; type checking and linting
passing where tools are available; architecture tests passing; documented external-contract evidence;
and no known fabricated-data path.

## C-11 — Decisions with lasting cost are recorded
Architecture, external-source selection, persistence format, GUI framework, and compatibility policy
require an ADR. Small reversible implementation choices do not.

## C-12 — Change taxonomy
Changes are labelled: FIX (specified behavior repaired), REFACTOR (behavior preserved), EVOLUTION
(new behavior), ARCH (architectural contract change), or REQ-CHANGE (normative behavior changed).
REQ-CHANGE requires updating affected specs and tests before code.
