from threading import RLock

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from evidencegraph.domain.errors import NotFoundError
from evidencegraph.domain.models import InvestigationRun, InvestigationRunStatus, new_id, utc_now
from evidencegraph.infrastructure.outbox import enqueue_investigation
from evidencegraph.infrastructure.sqlalchemy_repository import append_audit_event
from evidencegraph.infrastructure.tables import CaseTable, InvestigationRunTable


def _to_domain(row: InvestigationRunTable) -> InvestigationRun:
    return InvestigationRun(
        id=row.id,
        case_id=row.case_id,
        status=InvestigationRunStatus(row.status),
        requested_by=row.requested_by,
        requested_at=row.requested_at,
        started_at=row.started_at,
        completed_at=row.completed_at,
        error_code=row.error_code,
    )


class SqlAlchemyInvestigationQueue:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def enqueue(self, *, case_id: str, actor_id: str) -> InvestigationRun:
        with self._session_factory() as session, session.begin():
            case = session.scalar(
                select(CaseTable).where(CaseTable.id == case_id).with_for_update()
            )
            if case is None:
                raise NotFoundError("case was not found")
            row = enqueue_investigation(session, case_id=case_id, actor_id=actor_id)
            session.flush()
            append_audit_event(
                session,
                case_id=case_id,
                event_type="investigation.queued",
                actor_id=actor_id,
                payload={"run_id": row.id},
            )
            return _to_domain(row)

    def get(self, run_id: str) -> InvestigationRun | None:
        with self._session_factory() as session:
            row = session.get(InvestigationRunTable, run_id)
            return None if row is None else _to_domain(row)


class InMemoryInvestigationQueue:
    def __init__(self) -> None:
        self._runs: dict[str, InvestigationRun] = {}
        self._lock = RLock()

    def enqueue(self, *, case_id: str, actor_id: str) -> InvestigationRun:
        run = InvestigationRun(
            id=new_id("run"),
            case_id=case_id,
            status=InvestigationRunStatus.QUEUED,
            requested_by=actor_id,
            requested_at=utc_now(),
        )
        with self._lock:
            self._runs[run.id] = run
        return run

    def get(self, run_id: str) -> InvestigationRun | None:
        with self._lock:
            return self._runs.get(run_id)
