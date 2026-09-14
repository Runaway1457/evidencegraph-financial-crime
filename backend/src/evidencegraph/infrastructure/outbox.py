from datetime import UTC, datetime, timedelta
from enum import StrEnum

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from evidencegraph.domain.models import new_id
from evidencegraph.infrastructure.tables import InvestigationRunTable, WorkflowOutboxTable


class OutboxStatus(StrEnum):
    PENDING = "pending"
    LEASED = "leased"
    DISPATCHED = "dispatched"
    DEAD_LETTER = "dead_letter"


def enqueue_investigation(
    session: Session,
    *,
    case_id: str,
    actor_id: str,
) -> InvestigationRunTable:
    run = InvestigationRunTable(
        id=new_id("run"),
        case_id=case_id,
        status="queued",
        requested_by=actor_id,
    )
    message = WorkflowOutboxTable(
        id=new_id("outbox"),
        aggregate_id=run.id,
        event_type="investigation.requested",
        payload={"run_id": run.id, "case_id": case_id, "actor_id": actor_id},
        status=OutboxStatus.PENDING,
    )
    session.add_all((run, message))
    return run


def pending_messages_query(now: datetime, *, limit: int) -> Select[tuple[WorkflowOutboxTable]]:
    return (
        select(WorkflowOutboxTable)
        .where(
            WorkflowOutboxTable.status == OutboxStatus.PENDING,
            WorkflowOutboxTable.available_at <= now,
        )
        .order_by(WorkflowOutboxTable.created_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )


def lease_pending(
    session: Session,
    *,
    limit: int,
    lease_seconds: int,
    now: datetime | None = None,
) -> tuple[WorkflowOutboxTable, ...]:
    clock = now or datetime.now(UTC)
    messages = tuple(session.scalars(pending_messages_query(clock, limit=limit)))
    for message in messages:
        message.status = OutboxStatus.LEASED
        message.attempts += 1
        message.leased_until = clock + timedelta(seconds=lease_seconds)
    session.flush()
    return messages


def mark_dispatched(message: WorkflowOutboxTable, *, now: datetime | None = None) -> None:
    message.status = OutboxStatus.DISPATCHED
    message.dispatched_at = now or datetime.now(UTC)
    message.leased_until = None
    message.last_error = None


def mark_failed(
    message: WorkflowOutboxTable,
    *,
    error: str,
    max_attempts: int,
    retry_delay_seconds: int,
    now: datetime | None = None,
) -> None:
    clock = now or datetime.now(UTC)
    message.last_error = error[:2000]
    message.leased_until = None
    if message.attempts >= max_attempts:
        message.status = OutboxStatus.DEAD_LETTER
        return
    message.status = OutboxStatus.PENDING
    message.available_at = clock + timedelta(seconds=retry_delay_seconds)
