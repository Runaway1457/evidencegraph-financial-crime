from threading import RLock

from evidencegraph.domain.models import InvestigationCase


class InMemoryCaseRepository:
    def __init__(self) -> None:
        self._cases: dict[str, InvestigationCase] = {}
        self._lock = RLock()

    def save(self, case: InvestigationCase) -> None:
        with self._lock:
            self._cases[case.id] = case

    def get(self, case_id: str) -> InvestigationCase | None:
        with self._lock:
            return self._cases.get(case_id)

    def list(self) -> tuple[InvestigationCase, ...]:
        with self._lock:
            return tuple(
                sorted(self._cases.values(), key=lambda item: item.created_at, reverse=True)
            )
