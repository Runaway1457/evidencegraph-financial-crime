from dataclasses import replace

from evidencegraph.domain.models import (
    Entity,
    EntityKind,
    Evidence,
    EvidenceType,
    InvestigationCase,
    Relationship,
)
from evidencegraph.infrastructure.deterministic_agent import DeterministicInvestigator


def test_deterministic_baseline_emits_only_grounded_two_hop_paths() -> None:
    case = InvestigationCase.create(title="Meridian", description="", created_by="analyst")
    evidence = Evidence.create(
        case_id=case.id,
        evidence_type=EvidenceType.TRANSACTION,
        source="fixture",
        content_sha256="a" * 64,
        storage_key="case/evidence",
        ingested_by="analyst",
    )
    entities = tuple(
        Entity(
            id=entity_id,
            case_id=case.id,
            kind=EntityKind.ORGANIZATION,
            canonical_name=entity_id,
        )
        for entity_id in ("a", "b", "c")
    )
    relationships = (
        Relationship(
            id="r1",
            case_id=case.id,
            source_entity_id="a",
            target_entity_id="b",
            relationship_type="transferred_to",
            evidence_ids=(evidence.id,),
            confidence=0.94,
        ),
        Relationship(
            id="r2",
            case_id=case.id,
            source_entity_id="b",
            target_entity_id="c",
            relationship_type="transferred_to",
            evidence_ids=(evidence.id,),
            confidence=0.88,
        ),
    )
    aggregate = replace(
        case,
        evidence=(evidence,),
        entities=entities,
        relationships=relationships,
    )

    proposals = DeterministicInvestigator().propose(aggregate)

    assert len(proposals) == 1
    assert proposals[0].evidence_ids == (evidence.id,)
    assert proposals[0].confidence == 0.88
    assert "r1 and r2" in proposals[0].rationale


def test_deterministic_baseline_returns_no_claim_for_disconnected_edges() -> None:
    case = InvestigationCase.create(title="Empty", description="", created_by="analyst")
    assert DeterministicInvestigator().propose(case) == ()


def test_deterministic_baseline_rejects_two_cycles_and_caps_work() -> None:
    case = InvestigationCase.create(title="Bounded", description="", created_by="analyst")
    evidence = Evidence.create(
        case_id=case.id,
        evidence_type=EvidenceType.TRANSACTION,
        source="fixture",
        content_sha256="a" * 64,
        storage_key="case/bounded",
        ingested_by="analyst",
    )
    relationships = (
        Relationship("r1", case.id, "a", "b", "transfer", (evidence.id,), 0.9),
        Relationship("r2", case.id, "b", "a", "transfer", (evidence.id,), 0.9),
        Relationship("r3", case.id, "b", "c", "transfer", (evidence.id,), 0.8),
        Relationship("r4", case.id, "b", "d", "transfer", (evidence.id,), 0.7),
    )
    aggregate = replace(case, evidence=(evidence,), relationships=relationships)

    proposals = DeterministicInvestigator(max_proposals=1).propose(aggregate)

    assert len(proposals) == 1
    assert "r1 and r3" in proposals[0].rationale
