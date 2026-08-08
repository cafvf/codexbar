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


class SettingsError(CodexBarError):
    """Base class for expected settings failures."""


class SettingsValidationError(SettingsError):
    """A requested settings value is outside the supported domain."""


class SettingsDocumentError(SettingsError):
    """Persisted settings content is malformed or semantically invalid."""


class SettingsSchemaError(SettingsDocumentError):
    """Persisted settings schema is unsupported or structurally incompatible."""


class SettingsReadError(SettingsError):
    """Settings storage cannot be read."""


class SettingsWriteError(SettingsError):
    """Settings storage cannot be updated safely."""
