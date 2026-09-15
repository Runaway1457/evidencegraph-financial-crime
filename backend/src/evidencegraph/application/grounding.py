from collections.abc import Collection

from evidencegraph.application.ports import AgentFindingProposal
from evidencegraph.domain.errors import DomainError
from evidencegraph.domain.models import InvestigationCase


def validate_proposal(
    proposal: AgentFindingProposal,
    *,
    known_evidence: Collection[str],
) -> None:
    if not proposal.title.strip() or not proposal.rationale.strip():
        raise DomainError("agent proposals require title and rationale")
    if not proposal.evidence_ids:
        raise DomainError("agent proposals must cite evidence")
    if len(set(proposal.evidence_ids)) != len(proposal.evidence_ids):
        raise DomainError("agent proposal contains duplicate evidence citations")
    if missing := set(proposal.evidence_ids) - set(known_evidence):
        raise DomainError(f"agent cited unknown evidence: {sorted(missing)}")
    if not 0.0 <= proposal.confidence <= 1.0:
        raise DomainError("agent confidence must be between 0 and 1")


def validate_agent_proposals(
    case: InvestigationCase,
    proposals: tuple[AgentFindingProposal, ...],
) -> None:
    known_evidence = {item.id for item in case.evidence}
    for proposal in proposals:
        validate_proposal(proposal, known_evidence=known_evidence)
