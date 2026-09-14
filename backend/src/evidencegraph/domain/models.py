from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from string import hexdigits
from uuid import uuid4

from evidencegraph.domain.errors import DomainError


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def utc_now() -> datetime:
    return datetime.now(UTC)


def _require_sha256(value: str) -> None:
    if len(value) != 64 or any(char not in hexdigits for char in value):
        raise DomainError("content_sha256 must be a 64-character hexadecimal digest")


class CaseStatus(StrEnum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    CLOSED = "closed"


class EvidenceType(StrEnum):
    DOCUMENT = "document"
    TRANSACTION = "transaction"
    REGISTRY = "registry"
    BLOCKCHAIN = "blockchain"
    ANALYST_NOTE = "analyst_note"


class EntityKind(StrEnum):
    PERSON = "person"
    ORGANIZATION = "organization"
    ACCOUNT = "account"
    WALLET = "wallet"
    JURISDICTION = "jurisdiction"
    DOCUMENT = "document"


class FindingStatus(StrEnum):
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class Evidence:
    id: str
    case_id: str
    evidence_type: EvidenceType
    source: str
    content_sha256: str
    storage_key: str
    media_type: str
    size_bytes: int
    ingested_by: str
    ingested_at: datetime
    page: int | None = None
    bounding_box: tuple[float, float, float, float] | None = None

    def __post_init__(self) -> None:
        _require_sha256(self.content_sha256)
        if not self.source.strip() or not self.storage_key.strip():
            raise DomainError("evidence source and storage_key are required")
        if not self.media_type.strip() or self.size_bytes < 0:
            raise DomainError("evidence media_type and non-negative size_bytes are required")
        if self.page is not None and self.page < 1:
            raise DomainError("page must be greater than zero")

    @classmethod
    def create(
        cls,
        *,
        case_id: str,
        evidence_type: EvidenceType,
        source: str,
        content_sha256: str,
        storage_key: str,
        ingested_by: str,
        media_type: str = "application/octet-stream",
        size_bytes: int = 0,
        page: int | None = None,
        bounding_box: tuple[float, float, float, float] | None = None,
    ) -> "Evidence":
        return cls(
            id=new_id("ev"),
            case_id=case_id,
            evidence_type=evidence_type,
            source=source,
            content_sha256=content_sha256,
            storage_key=storage_key,
            media_type=media_type,
            size_bytes=size_bytes,
            ingested_by=ingested_by,
            ingested_at=utc_now(),
            page=page,
            bounding_box=bounding_box,
        )


@dataclass(frozen=True, slots=True)
class Entity:
    id: str
    case_id: str
    kind: EntityKind
    canonical_name: str
    attributes: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.canonical_name.strip():
            raise DomainError("canonical_name is required")


@dataclass(frozen=True, slots=True)
class Relationship:
    id: str
    case_id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    evidence_ids: tuple[str, ...]
    confidence: float

    def __post_init__(self) -> None:
        if self.source_entity_id == self.target_entity_id:
            raise DomainError("relationship endpoints must differ")
        if not self.evidence_ids:
            raise DomainError("relationship must cite at least one evidence item")
        if not 0.0 <= self.confidence <= 1.0:
            raise DomainError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class Finding:
    id: str
    case_id: str
    title: str
    rationale: str
    evidence_ids: tuple[str, ...]
    status: FindingStatus
    confidence: float
    proposed_by: str
    proposed_at: datetime
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.evidence_ids:
            raise DomainError("finding must cite at least one evidence item")
        if not 0.0 <= self.confidence <= 1.0:
            raise DomainError("confidence must be between 0 and 1")
        if self.status is not FindingStatus.PROPOSED and self.reviewed_by is None:
            raise DomainError("resolved findings require an independent reviewer")
        if self.reviewed_by is not None and self.reviewed_by == self.proposed_by:
            raise DomainError("four-eyes principle forbids self-review")

    def review(self, *, reviewer_id: str, decision: FindingStatus) -> "Finding":
        if decision is FindingStatus.PROPOSED:
            raise DomainError("review decision must resolve the finding")
        return replace(
            self,
            status=decision,
            reviewed_by=reviewer_id,
            reviewed_at=utc_now(),
        )


@dataclass(frozen=True, slots=True)
class InvestigationCase:
    id: str
    title: str
    description: str
    created_by: str
    created_at: datetime
    status: CaseStatus = CaseStatus.OPEN
    evidence: tuple[Evidence, ...] = ()
    entities: tuple[Entity, ...] = ()
    relationships: tuple[Relationship, ...] = ()
    findings: tuple[Finding, ...] = ()

    @classmethod
    def create(cls, *, title: str, description: str, created_by: str) -> "InvestigationCase":
        if not title.strip():
            raise DomainError("case title is required")
        return cls(
            id=new_id("case"),
            title=title.strip(),
            description=description.strip(),
            created_by=created_by,
            created_at=utc_now(),
        )

    def add_evidence(self, item: Evidence) -> "InvestigationCase":
        if item.case_id != self.id:
            raise DomainError("evidence belongs to another case")
        if any(existing.id == item.id for existing in self.evidence):
            raise DomainError("evidence id already exists")
        return replace(self, evidence=(*self.evidence, item))
