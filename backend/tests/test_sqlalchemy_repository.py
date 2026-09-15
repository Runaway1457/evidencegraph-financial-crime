from dataclasses import replace

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from evidencegraph.application.services import CaseService
from evidencegraph.config import Settings
from evidencegraph.domain.errors import ConcurrencyError
from evidencegraph.domain.models import (
    Entity,
    EntityKind,
    Evidence,
    EvidenceType,
    Finding,
    FindingStatus,
    InvestigationCase,
    Relationship,
    utc_now,
)
from evidencegraph.infrastructure.database import build_engine, build_session_factory
from evidencegraph.infrastructure.sqlalchemy_repository import SqlAlchemyCaseRepository
from evidencegraph.infrastructure.tables import AuditEventTable, Base, ChainOfCustodyTable


def repository() -> SqlAlchemyCaseRepository:
    engine = build_engine(Settings(environment="test", database_url="sqlite+pysqlite:///:memory:"))
    Base.metadata.create_all(engine)
    return SqlAlchemyCaseRepository(build_session_factory(engine))


def test_complete_case_aggregate_round_trips_through_sql() -> None:
    store = repository()
    case = InvestigationCase.create(
        title="Project Meridian",
        description="Synthetic investigation",
        created_by="analyst_1",
    )
    evidence = Evidence.create(
        case_id=case.id,
        evidence_type=EvidenceType.TRANSACTION,
        source="synthetic SWIFT fixture",
        content_sha256="a" * 64,
        storage_key=f"{case.id}/swift.json",
        media_type="application/json",
        size_bytes=241,
        ingested_by="analyst_1",
        page=1,
        bounding_box=(10.0, 20.0, 100.0, 80.0),
    )
    source = Entity(
        id="entity_source",
        case_id=case.id,
        kind=EntityKind.ORGANIZATION,
        canonical_name="Nova Meridian Ltd",
    )
    target = Entity(
        id="entity_target",
        case_id=case.id,
        kind=EntityKind.ORGANIZATION,
        canonical_name="Orion Trade GmbH",
    )
    relationship = Relationship(
        id="rel_transfer",
        case_id=case.id,
        source_entity_id=source.id,
        target_entity_id=target.id,
        relationship_type="transferred_to",
        evidence_ids=(evidence.id,),
        confidence=0.94,
    )
    finding = Finding(
        id="finding_circular_flow",
        case_id=case.id,
        title="Circular transfer flow",
        rationale="Grounded by a synthetic transfer record.",
        evidence_ids=(evidence.id,),
        status=FindingStatus.PROPOSED,
        confidence=0.91,
        proposed_by="analyst_1",
        generated_by="agent_investigator",
        proposed_at=utc_now(),
    )
    aggregate = replace(
        case,
        evidence=(evidence,),
        entities=(source, target),
        relationships=(relationship,),
        findings=(finding,),
    )

    store.save(aggregate)
    loaded = store.get(case.id)

    assert loaded is not None
    assert loaded.title == aggregate.title
    assert loaded.evidence[0].content_sha256 == "a" * 64
    assert loaded.evidence[0].bounding_box == (10.0, 20.0, 100.0, 80.0)
    assert loaded.relationships[0].evidence_ids == (evidence.id,)
    assert loaded.findings[0].evidence_ids == (evidence.id,)
    assert store.list()[0].id == case.id


def test_repository_save_updates_existing_aggregate() -> None:
    store = repository()
    case = InvestigationCase.create(title="Meridian", description="", created_by="analyst_1")
    store.save(case)

    updated = replace(case, description="Updated by an investigator", version=case.version + 1)
    store.save(updated)

    loaded = store.get(case.id)
    assert loaded is not None
    assert loaded.description == "Updated by an investigator"

    with pytest.raises(ConcurrencyError, match="changed"):
        store.save(replace(case, description="stale writer", version=case.version + 1))


def test_case_and_evidence_write_a_single_tamper_evident_audit_chain() -> None:
    engine = build_engine(Settings(environment="test", database_url="sqlite+pysqlite:///:memory:"))
    Base.metadata.create_all(engine)
    store = SqlAlchemyCaseRepository(build_session_factory(engine))
    service = CaseService(store)
    case = service.create_case(title="Meridian", description="", actor_id="analyst_1")

    evidence = service.ingest_evidence(
        case_id=case.id,
        content=b"source bytes",
        evidence_type=EvidenceType.DOCUMENT,
        source="upload",
        storage_key=f"{case.id}/source.pdf",
        actor_id="analyst_1",
        media_type="application/pdf",
    )

    with Session(engine) as session:
        events = session.scalars(
            select(AuditEventTable).order_by(AuditEventTable.occurred_at)
        ).all()
        custody = session.scalars(select(ChainOfCustodyTable)).all()

    assert [event.event_type for event in events] == ["case.created", "evidence.ingested"]
    assert events[1].previous_hash == events[0].event_hash
    assert custody[0].evidence_id == evidence.id
    assert custody[0].event_hash == events[1].event_hash

    with Session(engine) as session:
        event = session.scalar(select(AuditEventTable))
        assert event is not None
        event.payload = {"tampered": True}
        with pytest.raises(RuntimeError, match="append-only"):
            session.commit()
