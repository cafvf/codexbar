from typing import Protocol

from codexbar.domain.models import UsageSnapshot


class UsageProvider(Protocol):
    def get_usage(self) -> UsageSnapshot: ...
