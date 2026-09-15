from dataclasses import replace

import pytest

from evidencegraph.application.ports import AgentFindingProposal, PolicyDecision
from evidencegraph.application.services import InvestigationService
from evidencegraph.domain.errors import AuthorizationDeniedError, DomainError
from evidencegraph.domain.models import (
    Entity,
    EntityKind,
    Evidence,
    EvidenceType,
    FindingStatus,
    InvestigationCase,
    Relationship,
)
from evidencegraph.infrastructure.memory import InMemoryCaseRepository
from evidencegraph.infrastructure.policy import DevelopmentPolicy


class ProposalAgent:
    identity = "agent:test"

    def __init__(self, proposals: tuple[AgentFindingProposal, ...]) -> None:
        self.proposals = proposals
        self.calls = 0

    def propose(self, case: InvestigationCase) -> tuple[AgentFindingProposal, ...]:
        self.calls += 1
        return self.proposals


class DenyPolicy:
    def authorize(self, *, actor_id: str, action: str, case_id: str) -> PolicyDecision:
        return PolicyDecision(allowed=False, reason="clearance missing")


def grounded_case() -> InvestigationCase:
    case = InvestigationCase.create(title="Meridian", description="", created_by="analyst_1")
    evidence = Evidence.create(
        case_id=case.id,
        evidence_type=EvidenceType.TRANSACTION,
        source="synthetic",
        content_sha256="a" * 64,
        storage_key=f"{case.id}/transaction.json",
        ingested_by="analyst_1",
    )
    source = Entity(
        id="source",
        case_id=case.id,
        kind=EntityKind.ORGANIZATION,
        canonical_name="Nova Meridian",
    )
    middle = Entity(
        id="middle",
        case_id=case.id,
        kind=EntityKind.ORGANIZATION,
        canonical_name="Orion Trade",
    )
    target = Entity(
        id="target",
        case_id=case.id,
        kind=EntityKind.WALLET,
        canonical_name="0x7A91F",
    )
    first = Relationship(
        id="rel_1",
        case_id=case.id,
        source_entity_id=source.id,
        target_entity_id=middle.id,
        relationship_type="transferred_to",
        evidence_ids=(evidence.id,),
        confidence=0.94,
    )
    second = Relationship(
        id="rel_2",
        case_id=case.id,
        source_entity_id=middle.id,
        target_entity_id=target.id,
        relationship_type="transferred_to",
        evidence_ids=(evidence.id,),
        confidence=0.92,
    )
    return replace(
        case,
        evidence=(evidence,),
        entities=(source, middle, target),
        relationships=(first, second),
    )


def test_agent_proposal_is_grounded_persisted_and_idempotent() -> None:
    case = grounded_case()
    proposal = AgentFindingProposal(
        title="Layering path",
        rationale="Two evidence-backed transfers form a rapid path.",
        evidence_ids=(case.evidence[0].id,),
        confidence=0.91,
    )
    agent = ProposalAgent((proposal,))
    repository = InMemoryCaseRepository()
    repository.save(case)
    service = InvestigationService(repository, agent, DevelopmentPolicy())

    created = service.run(case_id=case.id, actor_id="analyst_1")
    replayed = service.run(case_id=case.id, actor_id="analyst_1")

    assert len(created) == 1
    assert created[0].proposed_by == "analyst_1"
    assert created[0].generated_by == "agent:test"
    assert replayed == ()
    assert len(repository.get(case.id).findings) == 1


def test_invalid_agent_batch_rolls_back_every_proposal() -> None:
    case = grounded_case()
    valid = AgentFindingProposal(
        title="Valid",
        rationale="Grounded",
        evidence_ids=(case.evidence[0].id,),
        confidence=0.8,
    )
    fabricated = AgentFindingProposal(
        title="Fabricated citation",
        rationale="Must be rejected",
        evidence_ids=("ev_missing",),
        confidence=0.99,
    )
    repository = InMemoryCaseRepository()
    repository.save(case)
    service = InvestigationService(
        repository,
        ProposalAgent((valid, fabricated)),
        DevelopmentPolicy(),
    )

    with pytest.raises(DomainError, match="unknown evidence"):
        service.run(case_id=case.id, actor_id="analyst_1")

    assert repository.get(case.id).findings == ()


def test_policy_denial_prevents_agent_execution() -> None:
    case = grounded_case()
    agent = ProposalAgent(())
    repository = InMemoryCaseRepository()
    repository.save(case)
    service = InvestigationService(repository, agent, DenyPolicy())

    with pytest.raises(AuthorizationDeniedError, match="clearance"):
        service.run(case_id=case.id, actor_id="analyst_1")

    assert agent.calls == 0


def test_independent_reviewer_can_confirm_proposed_finding() -> None:
    case = grounded_case()
    proposal = AgentFindingProposal(
        title="Layering path",
        rationale="Grounded path.",
        evidence_ids=(case.evidence[0].id,),
        confidence=0.91,
    )
    repository = InMemoryCaseRepository()
    repository.save(case)
    service = InvestigationService(repository, ProposalAgent((proposal,)), DevelopmentPolicy())
    finding = service.run(case_id=case.id, actor_id="analyst_1")[0]

    with pytest.raises(DomainError, match="self-review"):
        service.review(
            case_id=case.id,
            finding_id=finding.id,
            reviewer_id="analyst_1",
            decision=FindingStatus.CONFIRMED,
        )

    reviewed = service.review(
        case_id=case.id,
        finding_id=finding.id,
        reviewer_id="reviewer_2",
        decision=FindingStatus.CONFIRMED,
    )
    assert reviewed.status is FindingStatus.CONFIRMED
    assert reviewed.reviewed_by == "reviewer_2"
