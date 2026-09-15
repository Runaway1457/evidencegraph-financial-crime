from dataclasses import replace

from sqlalchemy import select
from sqlalchemy.orm import Session

from evidencegraph.application.services import InvestigationService
from evidencegraph.config import Settings
from evidencegraph.domain.models import (
    Entity,
    EntityKind,
    Evidence,
    EvidenceType,
    InvestigationCase,
    InvestigationRunStatus,
    Relationship,
)
from evidencegraph.infrastructure.database import build_engine, build_session_factory
from evidencegraph.infrastructure.deterministic_agent import DeterministicInvestigator
from evidencegraph.infrastructure.dispatcher import OutboxDispatcher
from evidencegraph.infrastructure.policy import DevelopmentPolicy
from evidencegraph.infrastructure.run_queue import SqlAlchemyInvestigationQueue
from evidencegraph.infrastructure.sqlalchemy_repository import SqlAlchemyCaseRepository
from evidencegraph.infrastructure.tables import Base, WorkflowOutboxTable


def test_outbox_dispatcher_completes_a_retry_safe_investigation() -> None:
    engine = build_engine(Settings(environment="test", database_url="sqlite+pysqlite:///:memory:"))
    Base.metadata.create_all(engine)
    factory = build_session_factory(engine)
    repository = SqlAlchemyCaseRepository(factory)
    queue = SqlAlchemyInvestigationQueue(factory)
    case = InvestigationCase.create(title="Meridian", description="", created_by="analyst_1")
    evidence = Evidence.create(
        case_id=case.id,
        evidence_type=EvidenceType.TRANSACTION,
        source="fixture",
        content_sha256="a" * 64,
        storage_key=f"{case.id}/transfer.json",
        ingested_by="analyst_1",
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
        Relationship("r1", case.id, "a", "b", "transferred_to", (evidence.id,), 0.9),
        Relationship("r2", case.id, "b", "c", "transferred_to", (evidence.id,), 0.8),
    )
    repository.save(
        replace(case, evidence=(evidence,), entities=entities, relationships=relationships)
    )
    run = queue.enqueue(case_id=case.id, actor_id="analyst_1")
    dispatcher = OutboxDispatcher(
        factory,
        InvestigationService(repository, DeterministicInvestigator(), DevelopmentPolicy()),
        lease_seconds=30,
        max_attempts=3,
    )

    assert dispatcher.dispatch_batch() == 1
    assert dispatcher.dispatch_batch() == 0

    completed = queue.get(run.id)
    assert completed is not None
    assert completed.status is InvestigationRunStatus.COMPLETED
    assert len(repository.get(case.id).findings) == 1
    with Session(engine) as session:
        outbox = session.scalar(select(WorkflowOutboxTable))
        assert outbox is not None
        assert outbox.status == "dispatched"
