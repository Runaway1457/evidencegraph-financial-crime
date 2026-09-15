from threading import RLock

from evidencegraph.domain.errors import ConcurrencyError
from evidencegraph.domain.models import CaseSummary, InvestigationCase


class InMemoryCaseRepository:
    def __init__(self) -> None:
        self._cases: dict[str, InvestigationCase] = {}
        self._lock = RLock()

    def save(self, case: InvestigationCase) -> None:
        with self._lock:
            current = self._cases.get(case.id)
            if current is not None and case.version != current.version + 1:
                raise ConcurrencyError("case changed after it was read")
            self._cases[case.id] = case

    def get(self, case_id: str) -> InvestigationCase | None:
        with self._lock:
            return self._cases.get(case_id)

    def list(self, *, limit: int = 50, offset: int = 0) -> tuple[InvestigationCase, ...]:
        with self._lock:
            ordered = sorted(self._cases.values(), key=lambda item: item.created_at, reverse=True)
            return tuple(ordered[offset : offset + limit])

    def list_summaries(self, *, limit: int, offset: int) -> tuple[CaseSummary, ...]:
        return tuple(case.summary() for case in self.list(limit=limit, offset=offset))
