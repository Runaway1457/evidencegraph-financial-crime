from collections.abc import Iterable

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, sessionmaker

from evidencegraph.domain.audit import GENESIS_HASH, AuditEvent
from evidencegraph.domain.errors import ConcurrencyError
from evidencegraph.domain.models import (
    CaseStatus,
    CaseSummary,
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
from evidencegraph.infrastructure.tables import (
    AuditEventTable,
    CaseTable,
    ChainOfCustodyTable,
    EntityTable,
    EvidenceTable,
    FindingEvidenceTable,
    FindingTable,
    RelationshipEvidenceTable,
    RelationshipTable,
)


def _bounding_box(values: list[float] | None) -> tuple[float, float, float, float] | None:
    if values is None:
        return None
    if len(values) != 4:
        raise ValueError("persisted evidence bounding_box must contain four coordinates")
    return (float(values[0]), float(values[1]), float(values[2]), float(values[3]))


def append_audit_event(
    session: Session,
    *,
    case_id: str,
    event_type: str,
    actor_id: str,
    payload: dict[str, object],
) -> AuditEvent:
    # Serialize the audit chain per case. Without this lock, two concurrent
    # writers can observe the same tail and create a forked hash chain.
    session.scalar(select(CaseTable.id).where(CaseTable.id == case_id).with_for_update())
    previous_hash = (
        session.scalar(
            select(AuditEventTable.event_hash)
            .where(AuditEventTable.case_id == case_id)
            .order_by(AuditEventTable.occurred_at.desc(), AuditEventTable.id.desc())
            .limit(1)
        )
        or GENESIS_HASH
    )
    event = AuditEvent.create(
        case_id=case_id,
        event_type=event_type,
        actor_id=actor_id,
        payload=payload,
        previous_hash=previous_hash,
    )
    session.add(
        AuditEventTable(
            id=event.id,
            case_id=event.case_id,
            event_type=event.event_type,
            actor_id=event.actor_id,
            occurred_at=event.occurred_at,
            payload=event.payload,
            previous_hash=event.previous_hash,
            event_hash=event.event_hash,
        )
    )
    session.flush()
    return event


class SqlAlchemyCaseRepository:
    """SQL-backed aggregate repository.

    Every save is a single database transaction. Cross-case references are
    rejected again by composite foreign keys in the relational model.
    """

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def save(self, case: InvestigationCase) -> None:
        with self._session_factory() as session, session.begin():
            current = session.scalar(
                select(CaseTable).where(CaseTable.id == case.id).with_for_update()
            )
            existing_evidence_ids = self._existing_ids(session, EvidenceTable, case.id)
            existing_finding_status = {
                finding_id: status
                for finding_id, status in session.execute(
                    select(FindingTable.id, FindingTable.status).where(
                        FindingTable.case_id == case.id
                    )
                )
            }
            if current is None:
                session.add(
                    CaseTable(
                        id=case.id,
                        title=case.title,
                        description=case.description,
                        status=case.status.value,
                        risk_score=0,
                        created_by=case.created_by,
                        created_at=case.created_at,
                        updated_at=utc_now(),
                        version=case.version,
                    )
                )
            else:
                if case.version != current.version + 1:
                    raise ConcurrencyError("case changed after it was read")
                result = session.execute(
                    update(CaseTable)
                    .where(CaseTable.id == case.id, CaseTable.version == current.version)
                    .values(
                        title=case.title,
                        description=case.description,
                        status=case.status.value,
                        updated_at=utc_now(),
                        version=case.version,
                    )
                )
                if getattr(result, "rowcount", 0) != 1:
                    raise ConcurrencyError("case changed while the update was being committed")
            self._save_evidence(session, case.evidence)
            self._save_entities(session, case.entities)
            session.flush()
            self._save_relationships(session, case.relationships)
            self._save_findings(session, case.findings)
            session.flush()
            if current is None:
                append_audit_event(
                    session,
                    case_id=case.id,
                    event_type="case.created",
                    actor_id=case.created_by,
                    payload={"title": case.title},
                )
            for evidence in case.evidence:
                if evidence.id in existing_evidence_ids:
                    continue
                event = append_audit_event(
                    session,
                    case_id=case.id,
                    event_type="evidence.ingested",
                    actor_id=evidence.ingested_by,
                    payload={
                        "evidence_id": evidence.id,
                        "content_sha256": evidence.content_sha256,
                        "source": evidence.source,
                        "size_bytes": evidence.size_bytes,
                    },
                )
                session.add(
                    ChainOfCustodyTable(
                        id=event.id,
                        case_id=case.id,
                        evidence_id=evidence.id,
                        action="ingested",
                        actor_id=evidence.ingested_by,
                        occurred_at=event.occurred_at,
                        content_sha256=evidence.content_sha256,
                        previous_hash=event.previous_hash,
                        event_hash=event.event_hash,
                    )
                )
            for finding in case.findings:
                previous_status = existing_finding_status.get(finding.id)
                if previous_status is None:
                    append_audit_event(
                        session,
                        case_id=case.id,
                        event_type="finding.proposed",
                        actor_id=finding.proposed_by,
                        payload={
                            "finding_id": finding.id,
                            "generated_by": finding.generated_by,
                            "signature_sha256": finding.signature_sha256,
                        },
                    )
                elif previous_status != finding.status.value:
                    append_audit_event(
                        session,
                        case_id=case.id,
                        event_type="finding.reviewed",
                        actor_id=finding.reviewed_by or "unknown-reviewer",
                        payload={"finding_id": finding.id, "decision": finding.status.value},
                    )

    def get(self, case_id: str) -> InvestigationCase | None:
        with self._session_factory() as session:
            row = session.get(CaseTable, case_id)
            return None if row is None else self._hydrate(session, row)

    def list(self, *, limit: int = 50, offset: int = 0) -> tuple[InvestigationCase, ...]:
        with self._session_factory() as session:
            rows = session.scalars(
                select(CaseTable).order_by(CaseTable.created_at.desc()).limit(limit).offset(offset)
            ).all()
            return tuple(self._hydrate(session, row) for row in rows)

    def list_summaries(self, *, limit: int, offset: int) -> tuple[CaseSummary, ...]:
        with self._session_factory() as session:
            rows = session.execute(
                select(CaseTable, func.count(EvidenceTable.id))
                .outerjoin(EvidenceTable, EvidenceTable.case_id == CaseTable.id)
                .group_by(CaseTable.id)
                .order_by(CaseTable.created_at.desc())
                .limit(limit)
                .offset(offset)
            ).all()
            return tuple(
                CaseSummary(
                    id=case.id,
                    title=case.title,
                    description=case.description,
                    created_by=case.created_by,
                    created_at=case.created_at,
                    status=CaseStatus(case.status),
                    evidence_count=evidence_count,
                    version=case.version,
                )
                for case, evidence_count in rows
            )

    @staticmethod
    def _existing_ids(session: Session, table: type[EvidenceTable], case_id: str) -> set[str]:
        return set(session.scalars(select(table.id).where(table.case_id == case_id)))

    @staticmethod
    def _save_evidence(session: Session, items: Iterable[Evidence]) -> None:
        for item in items:
            session.merge(
                EvidenceTable(
                    id=item.id,
                    case_id=item.case_id,
                    evidence_type=item.evidence_type.value,
                    source=item.source,
                    content_sha256=item.content_sha256,
                    storage_key=item.storage_key,
                    media_type=item.media_type,
                    size_bytes=item.size_bytes,
                    ingested_by=item.ingested_by,
                    ingested_at=item.ingested_at,
                    page=item.page,
                    bounding_box=list(item.bounding_box) if item.bounding_box else None,
                )
            )

    @staticmethod
    def _save_entities(session: Session, items: Iterable[Entity]) -> None:
        for item in items:
            session.merge(
                EntityTable(
                    id=item.id,
                    case_id=item.case_id,
                    kind=item.kind.value,
                    canonical_name=item.canonical_name,
                    attributes=item.attributes,
                )
            )

    @staticmethod
    def _save_relationships(session: Session, items: Iterable[Relationship]) -> None:
        for item in items:
            session.merge(
                RelationshipTable(
                    id=item.id,
                    case_id=item.case_id,
                    source_entity_id=item.source_entity_id,
                    target_entity_id=item.target_entity_id,
                    relationship_type=item.relationship_type,
                    confidence=item.confidence,
                    attributes={},
                )
            )
            session.flush()
            for evidence_id in item.evidence_ids:
                session.merge(
                    RelationshipEvidenceTable(
                        case_id=item.case_id,
                        relationship_id=item.id,
                        evidence_id=evidence_id,
                    )
                )

    @staticmethod
    def _save_findings(session: Session, items: Iterable[Finding]) -> None:
        for item in items:
            session.merge(
                FindingTable(
                    id=item.id,
                    case_id=item.case_id,
                    title=item.title,
                    rationale=item.rationale,
                    status=item.status.value,
                    confidence=item.confidence,
                    proposed_by=item.proposed_by,
                    generated_by=item.generated_by,
                    signature_sha256=item.signature_sha256,
                    proposed_at=item.proposed_at,
                    reviewed_by=item.reviewed_by,
                    reviewed_at=item.reviewed_at,
                )
            )
            session.flush()
            for evidence_id in item.evidence_ids:
                session.merge(
                    FindingEvidenceTable(
                        case_id=item.case_id,
                        finding_id=item.id,
                        evidence_id=evidence_id,
                    )
                )

    @staticmethod
    def _hydrate(session: Session, row: CaseTable) -> InvestigationCase:
        evidence_rows = session.scalars(
            select(EvidenceTable)
            .where(EvidenceTable.case_id == row.id)
            .order_by(EvidenceTable.ingested_at)
        ).all()
        entity_rows = session.scalars(
            select(EntityTable).where(EntityTable.case_id == row.id).order_by(EntityTable.id)
        ).all()
        relationship_rows = session.scalars(
            select(RelationshipTable)
            .where(RelationshipTable.case_id == row.id)
            .order_by(RelationshipTable.id)
        ).all()
        finding_rows = session.scalars(
            select(FindingTable)
            .where(FindingTable.case_id == row.id)
            .order_by(FindingTable.proposed_at)
        ).all()

        relationship_evidence: dict[str, list[str]] = {}
        for relationship_id, evidence_id in session.execute(
            select(
                RelationshipEvidenceTable.relationship_id,
                RelationshipEvidenceTable.evidence_id,
            ).where(RelationshipEvidenceTable.case_id == row.id)
        ):
            relationship_evidence.setdefault(relationship_id, []).append(evidence_id)

        finding_evidence: dict[str, list[str]] = {}
        for finding_id, evidence_id in session.execute(
            select(FindingEvidenceTable.finding_id, FindingEvidenceTable.evidence_id).where(
                FindingEvidenceTable.case_id == row.id
            )
        ):
            finding_evidence.setdefault(finding_id, []).append(evidence_id)

        evidence = tuple(
            Evidence(
                id=item.id,
                case_id=item.case_id,
                evidence_type=EvidenceType(item.evidence_type),
                source=item.source,
                content_sha256=item.content_sha256,
                storage_key=item.storage_key,
                media_type=item.media_type,
                size_bytes=item.size_bytes,
                ingested_by=item.ingested_by,
                ingested_at=item.ingested_at,
                page=item.page,
                bounding_box=_bounding_box(item.bounding_box),
            )
            for item in evidence_rows
        )
        entities = tuple(
            Entity(
                id=item.id,
                case_id=item.case_id,
                kind=EntityKind(item.kind),
                canonical_name=item.canonical_name,
                attributes={key: str(value) for key, value in item.attributes.items()},
            )
            for item in entity_rows
        )
        relationships = tuple(
            Relationship(
                id=item.id,
                case_id=item.case_id,
                source_entity_id=item.source_entity_id,
                target_entity_id=item.target_entity_id,
                relationship_type=item.relationship_type,
                evidence_ids=tuple(relationship_evidence.get(item.id, ())),
                confidence=item.confidence,
            )
            for item in relationship_rows
        )
        findings = tuple(
            Finding(
                id=item.id,
                case_id=item.case_id,
                title=item.title,
                rationale=item.rationale,
                evidence_ids=tuple(finding_evidence.get(item.id, ())),
                status=FindingStatus(item.status),
                confidence=item.confidence,
                proposed_by=item.proposed_by,
                generated_by=item.generated_by,
                proposed_at=item.proposed_at,
                reviewed_by=item.reviewed_by,
                reviewed_at=item.reviewed_at,
            )
            for item in finding_rows
        )
        return InvestigationCase(
            id=row.id,
            title=row.title,
            description=row.description,
            created_by=row.created_by,
            created_at=row.created_at,
            status=CaseStatus(row.status),
            version=row.version,
            evidence=evidence,
            entities=entities,
            relationships=relationships,
            findings=findings,
        )
