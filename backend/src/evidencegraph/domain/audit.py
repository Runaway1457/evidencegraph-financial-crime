from dataclasses import dataclass
from datetime import datetime
from typing import Self

from evidencegraph.domain.errors import DomainError
from evidencegraph.domain.hashing import canonical_sha256
from evidencegraph.domain.models import new_id, utc_now

GENESIS_HASH = "0" * 64


def _event_hash(
    *,
    event_id: str,
    case_id: str,
    event_type: str,
    actor_id: str,
    occurred_at: datetime,
    payload: dict[str, object],
    previous_hash: str,
) -> str:
    return canonical_sha256(
        {
            "id": event_id,
            "case_id": case_id,
            "event_type": event_type,
            "actor_id": actor_id,
            "occurred_at": occurred_at.isoformat(),
            "payload": payload,
            "previous_hash": previous_hash,
        }
    )


@dataclass(frozen=True, slots=True)
class AuditEvent:
    id: str
    case_id: str
    event_type: str
    actor_id: str
    occurred_at: datetime
    payload: dict[str, object]
    previous_hash: str
    event_hash: str

    @classmethod
    def create(
        cls,
        *,
        case_id: str,
        event_type: str,
        actor_id: str,
        payload: dict[str, object],
        previous_hash: str = GENESIS_HASH,
        occurred_at: datetime | None = None,
    ) -> Self:
        if not case_id or not event_type or not actor_id:
            raise DomainError("case_id, event_type, and actor_id are required")
        if len(previous_hash) != 64:
            raise DomainError("previous_hash must be a SHA-256 digest")

        event_id = new_id("audit")
        event_time = occurred_at or utc_now()
        safe_payload = dict(payload)
        digest = _event_hash(
            event_id=event_id,
            case_id=case_id,
            event_type=event_type,
            actor_id=actor_id,
            occurred_at=event_time,
            payload=safe_payload,
            previous_hash=previous_hash,
        )
        return cls(
            id=event_id,
            case_id=case_id,
            event_type=event_type,
            actor_id=actor_id,
            occurred_at=event_time,
            payload=safe_payload,
            previous_hash=previous_hash,
            event_hash=digest,
        )

    def has_valid_hash(self) -> bool:
        return self.event_hash == _event_hash(
            event_id=self.id,
            case_id=self.case_id,
            event_type=self.event_type,
            actor_id=self.actor_id,
            occurred_at=self.occurred_at,
            payload=self.payload,
            previous_hash=self.previous_hash,
        )


class AuditChain:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)

    def append(
        self,
        *,
        case_id: str,
        event_type: str,
        actor_id: str,
        payload: dict[str, object],
    ) -> AuditEvent:
        previous_hash = self._events[-1].event_hash if self._events else GENESIS_HASH
        event = AuditEvent.create(
            case_id=case_id,
            event_type=event_type,
            actor_id=actor_id,
            payload=payload,
            previous_hash=previous_hash,
        )
        self._events.append(event)
        return event

    def verify(self) -> bool:
        previous_hash = GENESIS_HASH
        for event in self._events:
            if event.previous_hash != previous_hash or not event.has_valid_hash():
                return False
            previous_hash = event.event_hash
        return True
