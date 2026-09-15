from datetime import UTC, datetime

from sqlalchemy.orm import Session, sessionmaker

from evidencegraph.application.services import InvestigationService
from evidencegraph.infrastructure.outbox import (
    OutboxStatus,
    lease_pending,
    mark_dispatched,
    mark_failed,
)
from evidencegraph.infrastructure.sqlalchemy_repository import append_audit_event
from evidencegraph.infrastructure.tables import InvestigationRunTable, WorkflowOutboxTable


class OutboxDispatcher:
    """Runs leased workflow messages with retry-safe finding persistence."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        investigation_service: InvestigationService,
        *,
        lease_seconds: int,
        max_attempts: int,
    ) -> None:
        self._session_factory = session_factory
        self._investigation_service = investigation_service
        self._lease_seconds = lease_seconds
        self._max_attempts = max_attempts

    def dispatch_batch(self, *, limit: int = 10) -> int:
        with self._session_factory() as session, session.begin():
            message_ids = tuple(
                message.id
                for message in lease_pending(
                    session,
                    limit=limit,
                    lease_seconds=self._lease_seconds,
                )
            )
        for message_id in message_ids:
            self._dispatch_one(message_id)
        return len(message_ids)

    def _dispatch_one(self, message_id: str) -> None:
        with self._session_factory() as session, session.begin():
            message = session.get(WorkflowOutboxTable, message_id)
            if message is None or message.status != OutboxStatus.LEASED:
                return
            run = session.get(InvestigationRunTable, message.aggregate_id)
            if run is None:
                mark_failed(
                    message,
                    error="run_not_found",
                    max_attempts=1,
                    retry_delay_seconds=0,
                )
                return
            run.status = "running"
            run.started_at = datetime.now(UTC)
            payload = dict(message.payload)

        try:
            self._investigation_service.run(
                case_id=str(payload["case_id"]),
                actor_id=str(payload["actor_id"]),
            )
        except Exception as exc:
            with self._session_factory() as session, session.begin():
                message = session.get(WorkflowOutboxTable, message_id)
                run = session.get(InvestigationRunTable, str(payload["run_id"]))
                if message is None or run is None:
                    return
                mark_failed(
                    message,
                    error=type(exc).__name__,
                    max_attempts=self._max_attempts,
                    retry_delay_seconds=min(2**message.attempts, 300),
                )
                run.status = "failed" if message.status == OutboxStatus.DEAD_LETTER else "queued"
                run.error_code = type(exc).__name__
                append_audit_event(
                    session,
                    case_id=run.case_id,
                    event_type="investigation.failed",
                    actor_id=run.requested_by,
                    payload={
                        "run_id": run.id,
                        "error_code": run.error_code,
                        "retryable": run.status == "queued",
                    },
                )
            return

        with self._session_factory() as session, session.begin():
            message = session.get(WorkflowOutboxTable, message_id)
            run = session.get(InvestigationRunTable, str(payload["run_id"]))
            if message is None or run is None:
                return
            mark_dispatched(message)
            run.status = "completed"
            run.completed_at = datetime.now(UTC)
            run.error_code = None
            append_audit_event(
                session,
                case_id=run.case_id,
                event_type="investigation.completed",
                actor_id=run.requested_by,
                payload={"run_id": run.id},
            )
