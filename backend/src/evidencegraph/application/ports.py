from dataclasses import dataclass
from typing import Protocol

from evidencegraph.domain.models import InvestigationCase


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

    def list(self) -> tuple[InvestigationCase, ...]: ...


class InvestigatorAgent(Protocol):
    @property
    def identity(self) -> str: ...

    def propose(self, case: InvestigationCase) -> tuple[AgentFindingProposal, ...]: ...


class PolicyPort(Protocol):
    def authorize(self, *, actor_id: str, action: str, case_id: str) -> PolicyDecision: ...
