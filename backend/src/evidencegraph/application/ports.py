from dataclasses import dataclass
from typing import Protocol

from evidencegraph.domain.models import CaseSummary, InvestigationCase, InvestigationRun


@dataclass(frozen=True, slots=True)
class AgentFindingProposal:
    title: str
    rationale: str
    evidence_ids: tuple[str, ...]
    confidence: float


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    reason: str
    obligations: tuple[str, ...] = ()


class CaseRepository(Protocol):
    def save(self, case: InvestigationCase) -> None: ...

    def get(self, case_id: str) -> InvestigationCase | None: ...

    def list(self, *, limit: int = 50, offset: int = 0) -> tuple[InvestigationCase, ...]: ...

    def list_summaries(self, *, limit: int, offset: int) -> tuple[CaseSummary, ...]: ...


class InvestigatorAgent(Protocol):
    @property
    def identity(self) -> str: ...

    def propose(self, case: InvestigationCase) -> tuple[AgentFindingProposal, ...]: ...


class PolicyPort(Protocol):
    def authorize(self, *, actor_id: str, action: str, case_id: str) -> PolicyDecision: ...


class ObjectStore(Protocol):
    def put(self, key: str, content: bytes) -> None: ...

    def delete(self, key: str) -> None: ...


class InvestigationQueue(Protocol):
    def enqueue(self, *, case_id: str, actor_id: str) -> InvestigationRun: ...

    def get(self, run_id: str) -> InvestigationRun | None: ...
