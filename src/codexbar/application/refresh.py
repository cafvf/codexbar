from codexbar.application.use_cases import GetCurrentUsage, GetUsageQuery
from codexbar.domain.errors import UsageSourceError
from codexbar.domain.models import UsageSnapshot


class RefreshCoordinator:
    def __init__(self, use_case: GetCurrentUsage) -> None:
        self._use_case = use_case
        self._last_valid: UsageSnapshot | None = None

    def refresh(self, query: GetUsageQuery | None = None) -> UsageSnapshot:
        try:
            snapshot = self._use_case.execute(query)
        except UsageSourceError:
            if self._last_valid is None:
                raise
            return self._last_valid.as_stale()
        self._last_valid = snapshot
        return snapshot
