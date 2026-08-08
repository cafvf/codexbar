class CodexBarError(Exception):
    """Base class for expected CodexBar failures."""


class UsageError(CodexBarError):
    """Base class for usage-query failures."""


class UsageSourceError(UsageError):
    """Failure while obtaining data from a usage source."""


class UsageSourceUnavailableError(UsageSourceError):
    """Configured source cannot be reached or executed."""


class UsageCommandError(UsageSourceError):
    """External Codex command/protocol returned a known execution failure."""


class UsageAuthenticationError(UsageSourceError):
    """Source indicates missing or invalid authentication."""


class UsageTimeoutError(UsageSourceError):
    """Source did not answer within the configured deadline."""


class UsageParseError(UsageError):
    """Source data cannot be safely parsed."""


class UsageSchemaError(UsageParseError):
    """Source data shape is unsupported or incomplete."""
