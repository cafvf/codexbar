# v1.5 Upstream Contract — Codex reset credits

Status: verified source note
Verified: 2026-08-10
Upstream: OpenAI Codex app-server `main`

## Authoritative sources

Primary:
- `codex-rs/app-server/README.md`

Generated protocol evidence:
- `codex-rs/app-server-protocol/schema/typescript/v2/GetAccountRateLimitsResponse.ts`
- `RateLimitResetCreditsSummary.ts`
- `RateLimitResetCredit.ts`
- `RateLimitResetCreditStatus.ts`
- `RateLimitResetType.ts`

## Read method

`account/rateLimits/read`

A response may contain:
- usage `rateLimits`;
- optional `rateLimitResetCredits`.

Reset-credit semantics:

- `rateLimitResetCredits == null`: reset-credit capability/data were not provided.
- `availableCount`: authoritative non-negative count of currently available earned resets.
- `credits == null`: count is known, per-credit details are not returned.
- `credits == []`: a detail array was returned and contains zero available rows.
- backend may cap detailed rows; therefore `len(credits)` may be less than `availableCount`.
- when detailed rows are returned, each credit contains:
  - opaque `id`;
  - `resetType`;
  - `status`;
  - mandatory Unix-seconds `grantedAt`;
  - nullable Unix-seconds `expiresAt`;
  - nullable `title`;
  - nullable `description`.

`expiresAt == null` means the detailed credit does not expire. It does not mean "expiry unknown".

Current generated enum values include:
- reset type: `codexRateLimits`, `unknown`;
- status: `available`, `redeeming`, `redeemed`, `unknown`.

CodexBar SHOULD remain tolerant of future source values at its raw parsing boundary.

Reset-credit detail is snapshot-only. `account/rateLimits/updated` is a sparse rate-limit notification and
is not an authoritative reset-credit-detail stream.

## Detail coverage derivation

Given authoritative `availableCount = N` and a returned detail array of unique rows with size `n`:

- `credits == null` -> `COUNT_ONLY`;
- `credits != null` and `n < N` -> `DETAILS_PARTIAL`;
- `credits != null` and `n == N` -> `DETAILS_COMPLETE`;
- `n > N` -> inconsistent upstream structure and SHALL fail reset-detail normalization safely.

This coverage classification is a CodexBar interpretation of the documented count/capping semantics.

## Consume method

`account/rateLimitResetCredit/consume`

Parameters:
- non-empty `idempotencyKey`;
- optional non-empty opaque `creditId`.

The upstream contract recommends one UUID per logical redemption attempt and reuse of that same key when
retrying the same attempt.

Documented outcomes:
- `reset`;
- `alreadyRedeemed`;
- `nothingToReset`;
- `noCredit`.

`reset` and `alreadyRedeemed` are successful/idempotent completion states and require a fresh
`account/rateLimits/read`.

CodexBar SHALL NOT infer the post-action usage/reset state from the consume response.

## CodexBar boundary

CodexBar v1.5 SHALL depend on supported local app-server methods, not private ChatGPT endpoints.

Generated protocol artifacts are specific to the installed Codex version. Implementation tests SHOULD use
fixtures compatible with the supported protocol while parser behavior remains defensive against optional
capability absence and future unknown source values.
