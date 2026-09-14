from typing import Protocol

from evidencegraph.domain.models import InvestigationCase


class CaseRepository(Protocol):
    def save(self, case: InvestigationCase) -> None: ...

    def get(self, case_id: str) -> InvestigationCase | None: ...

    def list(self) -> tuple[InvestigationCase, ...]: ...
