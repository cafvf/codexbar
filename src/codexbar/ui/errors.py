from codexbar.domain.errors import CodexBarError


class UiError(CodexBarError):
    """Base class for presentation/runtime errors."""


class GuiDependencyError(UiError):
    pass


class SystemTrayUnavailableError(UiError):
    pass
