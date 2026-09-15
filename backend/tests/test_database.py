import pytest
from sqlalchemy import Engine, create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from evidencegraph.infrastructure.tables import (
    Base,
    CaseTable,
    EvidenceTable,
    FindingEvidenceTable,
    FindingTable,
)


def sqlite_engine() -> Engine:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection: object, connection_record: object) -> None:
        del connection_record
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    return engine


def case(case_id: str) -> CaseTable:
    return CaseTable(
        id=case_id,
        title=case_id,
        description="Synthetic case",
        status="open",
        risk_score=0,
        created_by="analyst_1",
    )


def evidence(case_id: str, evidence_id: str) -> EvidenceTable:
    return EvidenceTable(
        id=evidence_id,
        case_id=case_id,
        evidence_type="document",
        source="fixture",
        content_sha256="a" * 64,
        storage_key=f"{case_id}/{evidence_id}",
        media_type="application/pdf",
        size_bytes=100,
        ingested_by="analyst_1",
    )


def finding(case_id: str, finding_id: str) -> FindingTable:
    return FindingTable(
        id=finding_id,
        case_id=case_id,
        title="Suspicious circular flow",
        rationale="Grounded synthetic rationale",
        status="proposed",
        confidence=0.9,
        proposed_by="analyst_1",
        generated_by="agent_1",
        signature_sha256="b" * 64,
    )


def test_same_case_finding_evidence_is_persisted() -> None:
    engine = sqlite_engine()
    with Session(engine) as session, session.begin():
        session.add(case("case_1"))
        session.add(evidence("case_1", "ev_1"))
        session.add(finding("case_1", "finding_1"))
        session.flush()
        session.add(
            FindingEvidenceTable(
                case_id="case_1",
                finding_id="finding_1",
                evidence_id="ev_1",
            )
        )

    with Session(engine) as session:
        links = session.scalars(select(FindingEvidenceTable)).all()
        assert len(links) == 1


def test_cross_case_evidence_reference_is_rejected_by_database() -> None:
    engine = sqlite_engine()
    with Session(engine) as session:
        session.add_all(
            (
                case("case_1"),
                case("case_2"),
                evidence("case_1", "ev_1"),
                finding("case_2", "finding_2"),
            )
        )
        session.commit()
        session.add(
            FindingEvidenceTable(
                case_id="case_2",
                finding_id="finding_2",
                evidence_id="ev_1",
            )
        )
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("cross-case evidence link unexpectedly succeeded")


def test_duplicate_finding_signature_is_rejected_within_a_case() -> None:
    engine = sqlite_engine()
    with Session(engine) as session:
        session.add(case("case_1"))
        session.add_all((finding("case_1", "finding_1"), finding("case_1", "finding_2")))
        with pytest.raises(IntegrityError):
            session.commit()
