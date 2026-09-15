import pytest

from evidencegraph.domain.errors import DomainError
from evidencegraph.domain.hashing import canonical_sha256, sha256_bytes
from evidencegraph.domain.models import (
    Evidence,
    EvidenceType,
    Finding,
    FindingStatus,
    InvestigationCase,
    Relationship,
    utc_now,
)


def test_sha256_is_stable() -> None:
    assert sha256_bytes(b"evidence") == sha256_bytes(b"evidence")
    assert canonical_sha256({"b": 2, "a": 1}) == canonical_sha256({"a": 1, "b": 2})


def test_evidence_rejects_invalid_digest() -> None:
    with pytest.raises(DomainError, match="64-character"):
        Evidence.create(
            case_id="case_1",
            evidence_type=EvidenceType.DOCUMENT,
            source="upload",
            content_sha256="invalid",
            storage_key="case_1/document.pdf",
            ingested_by="analyst_1",
        )


def test_relationship_requires_evidence() -> None:
    with pytest.raises(DomainError, match="cite"):
        Relationship(
            id="rel_1",
            case_id="case_1",
            source_entity_id="entity_1",
            target_entity_id="entity_2",
            relationship_type="transferred_to",
            evidence_ids=(),
            confidence=0.9,
        )


def test_finding_enforces_four_eyes() -> None:
    finding = Finding(
        id="finding_1",
        case_id="case_1",
        title="Circular flow",
        rationale="Three transfers return funds to the originator.",
        evidence_ids=("ev_1",),
        status=FindingStatus.PROPOSED,
        confidence=0.91,
        proposed_by="analyst_1",
        proposed_at=utc_now(),
    )

    with pytest.raises(DomainError, match="self-review"):
        finding.review(reviewer_id="analyst_1", decision=FindingStatus.CONFIRMED)

    confirmed = finding.review(reviewer_id="analyst_2", decision=FindingStatus.CONFIRMED)
    assert confirmed.reviewed_by == "analyst_2"


def test_case_accepts_only_its_own_evidence() -> None:
    case = InvestigationCase.create(title="Meridian", description="", created_by="analyst_1")
    foreign = Evidence.create(
        case_id="case_other",
        evidence_type=EvidenceType.DOCUMENT,
        source="upload",
        content_sha256="a" * 64,
        storage_key="foreign.pdf",
        ingested_by="analyst_1",
    )
    with pytest.raises(DomainError, match="another case"):
        case.add_evidence(foreign)
