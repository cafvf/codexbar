# REQ-ALERT-001 — Notification transport diagnosis

The alert state machine has been observed producing LOW and EXHAUSTED transitions, but the target desktop did
not visibly present notifications.

Before changing transports, verify whether the freedesktop notification server accepts the actual D-Bus
request:

```bash
uv run python scripts/diagnose_notifications.py
```

Expected successful transport evidence includes:
- session bus connected: True;
- notification interface valid: True;
- GetServerInformation returns ReplyMessage;
- GetCapabilities returns ReplyMessage;
- Notify raw reply is ReplyMessage;
- Notify reply contains one positive integer notification id;
- final PASS message.

If Notify returns an ErrorMessage, preserve the complete diagnostic output: it identifies a D-Bus signature,
marshalling, or server-contract failure.

If Notify returns a positive notification id but no popup is visible, the application-to-server transport is
working and the remaining issue is desktop presentation (GNOME notification settings, Do Not Disturb,
grouping, shell policy, or similar).

As an independent desktop-control check, if `notify-send` is installed:

```bash
notify-send "CodexBar control test" "If this is invisible too, inspect GNOME notification settings."
```

Do not interpret a successful transition event alone as AC-ALERT-026 evidence. The desktop must visibly
present LOW and EXHAUSTED notifications.
