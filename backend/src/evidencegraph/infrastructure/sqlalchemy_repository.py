from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from evidencegraph.domain.models import (
    CaseStatus,
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
    CaseTable,
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


class SqlAlchemyCaseRepository:
    """SQL-backed aggregate repository.

    Every save is a single database transaction. Cross-case references are
    rejected again by composite foreign keys in the relational model.
    """

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def save(self, case: InvestigationCase) -> None:
        with self._session_factory() as session, session.begin():
            session.merge(
                CaseTable(
                    id=case.id,
                    title=case.title,
                    description=case.description,
                    status=case.status.value,
                    risk_score=0,
                    created_by=case.created_by,
                    created_at=case.created_at,
                    updated_at=utc_now(),
                )
            )
            self._save_evidence(session, case.evidence)
            self._save_entities(session, case.entities)
            session.flush()
            self._save_relationships(session, case.relationships)
            self._save_findings(session, case.findings)

    def get(self, case_id: str) -> InvestigationCase | None:
        with self._session_factory() as session:
            row = session.get(CaseTable, case_id)
            return None if row is None else self._hydrate(session, row)

    def list(self) -> tuple[InvestigationCase, ...]:
        with self._session_factory() as session:
            rows = session.scalars(select(CaseTable).order_by(CaseTable.created_at.desc())).all()
            return tuple(self._hydrate(session, row) for row in rows)

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
                evidence_ids=tuple(
                    session.scalars(
                        select(RelationshipEvidenceTable.evidence_id).where(
                            RelationshipEvidenceTable.case_id == row.id,
                            RelationshipEvidenceTable.relationship_id == item.id,
                        )
                    )
                ),
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
                evidence_ids=tuple(
                    session.scalars(
                        select(FindingEvidenceTable.evidence_id).where(
                            FindingEvidenceTable.case_id == row.id,
                            FindingEvidenceTable.finding_id == item.id,
                        )
                    )
                ),
                status=FindingStatus(item.status),
                confidence=item.confidence,
                proposed_by=item.proposed_by,
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
            evidence=evidence,
            entities=entities,
            relationships=relationships,
            findings=findings,
        )
