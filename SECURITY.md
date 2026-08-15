# Security Policy

## Supported release

The current validated release is CodexBar **1.8.0**. Security fixes, if required,
are expected to be delivered as maintenance releases from the current stable
line unless a later release supersedes it.

## Reporting a vulnerability

Do **not** publish credentials, Codex authentication material, private account
payloads, reset-credit identifiers, or other sensitive local data in a public
GitHub issue.

If the repository's GitHub **Security** tab offers a private vulnerability
reporting action, use that channel. If no private reporting action is available,
contact the maintainer through the GitHub profile associated with this
repository, or open a minimal public issue that contains no sensitive details
and asks for a private contact channel.

A useful report includes, when safe to share:

- affected CodexBar version;
- operating system and desktop/session type;
- whether the problem reproduces with the current stable tag;
- a minimal reproduction;
- security impact;
- sanitized diagnostic output.

## Credential boundary

CodexBar does not own or manage Codex credentials. Raw credentials and private
authentication material must not be copied into CodexBar History, settings,
diagnostic fixtures, reset-ledger evidence, native-helper messages, repository
logs, or bug reports.

## Local data

CodexBar stores local application data such as settings, usage History, and the
reset event ledger in user-local storage. Uninstall intentionally preserves
persistent user data unless the user explicitly removes it.

## Repository hygiene

Local development/runtime state such as `.omx/`, local logs, crash dumps,
diagnostic captures, local databases, credentials, and raw provider/account
payloads must not be committed unless a deliberately sanitized fixture is
required for a test.

If a secret is discovered in Git history, removing the file from the current
tree is not sufficient: revoke/rotate the secret first, then assess whether
history rewriting is warranted.
