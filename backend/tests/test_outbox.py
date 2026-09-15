from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from evidencegraph.infrastructure.outbox import (
    OutboxStatus,
    enqueue_investigation,
    lease_pending,
    mark_dispatched,
    mark_failed,
)
from evidencegraph.infrastructure.tables import (
    Base,
    CaseTable,
    InvestigationRunTable,
    WorkflowOutboxTable,
)


def add_case(session: Session) -> None:
    session.add(
        CaseTable(
            id="case_1",
            title="Meridian",
            description="Synthetic",
            status="open",
            risk_score=87,
            created_by="analyst_1",
        )
    )


def test_run_and_outbox_message_commit_atomically() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session, session.begin():
        add_case(session)
        run = enqueue_investigation(session, case_id="case_1", actor_id="analyst_1")
        run_id = run.id

    with Session(engine) as session:
        stored_run = session.get(InvestigationRunTable, run_id)
        message = session.scalar(select(WorkflowOutboxTable))
        assert stored_run is not None
        assert message is not None
        assert message.payload["run_id"] == run_id
        assert message.status == OutboxStatus.PENDING


def test_outbox_leasing_success_retry_and_dead_letter() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session, session.begin():
        add_case(session)
        enqueue_investigation(session, case_id="case_1", actor_id="analyst_1")

    # Advance beyond the generated available_at without coupling the test to
    # wall-clock time or changing the dispatcher's production semantics.
    clock = datetime.now(UTC) + timedelta(seconds=1)

    with Session(engine) as session, session.begin():
        leased = lease_pending(session, limit=10, lease_seconds=30, now=clock)
        message = leased[0]
        assert message.status == OutboxStatus.LEASED
        assert message.attempts == 1
        mark_failed(
            message,
            error="temporal unavailable",
            max_attempts=2,
            retry_delay_seconds=5,
            now=clock,
        )
        assert message.status == OutboxStatus.PENDING

    with Session(engine) as session, session.begin():
        message = session.scalar(select(WorkflowOutboxTable))
        assert message is not None
        message.available_at = clock
        leased = lease_pending(session, limit=10, lease_seconds=30, now=clock)
        message = leased[0]
        mark_failed(
            message,
            error="still unavailable",
            max_attempts=2,
            retry_delay_seconds=5,
            now=clock,
        )
        assert message.status == OutboxStatus.DEAD_LETTER

    with Session(engine) as session, session.begin():
        message = session.scalar(select(WorkflowOutboxTable))
        assert message is not None
        message.status = OutboxStatus.LEASED
        mark_dispatched(message, now=clock)
        assert message.status == OutboxStatus.DISPATCHED
        assert message.dispatched_at == clock
