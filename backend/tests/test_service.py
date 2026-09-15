import pytest

from evidencegraph.application.services import CaseService
from evidencegraph.domain.errors import NotFoundError
from evidencegraph.domain.models import EvidenceType
from evidencegraph.infrastructure.memory import InMemoryCaseRepository


def test_case_and_evidence_lifecycle() -> None:
    service = CaseService(InMemoryCaseRepository())
    case = service.create_case(
        title="Project Meridian",
        description="Synthetic case",
        actor_id="a1",
    )

    evidence = service.ingest_evidence(
        case_id=case.id,
        content=b"synthetic transaction",
        evidence_type=EvidenceType.TRANSACTION,
        source="fixture",
        storage_key=f"{case.id}/tx.json",
        actor_id="a1",
    )

    hydrated = service.get_case(case.id)
    assert hydrated.evidence == (evidence,)
    assert service.list_cases() == (hydrated,)


def test_missing_case_is_explicit() -> None:
    service = CaseService(InMemoryCaseRepository())
    with pytest.raises(NotFoundError):
        service.get_case("case_missing")
