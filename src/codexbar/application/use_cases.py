from dataclasses import dataclass

from codexbar.application.ports import UsageProvider
from codexbar.domain.models import UsageSnapshot


@dataclass(frozen=True, slots=True)
class GetUsageQuery:
    force_refresh: bool = False


class GetCurrentUsage:
    def __init__(self, provider: UsageProvider) -> None:
        self._provider = provider

    def execute(self, query: GetUsageQuery | None = None) -> UsageSnapshot:
        # force_refresh is part of the stable application input contract. Cache-aware providers or
        # coordinators may consume it later; the base provider always performs a query.
        _ = query or GetUsageQuery()
        return self._provider.get_usage()
