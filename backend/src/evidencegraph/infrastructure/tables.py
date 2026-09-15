from datetime import UTC, datetime

from sqlalchemy import (
    DDL,
    JSON,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class CaseTable(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        CheckConstraint("risk_score BETWEEN 0 AND 100", name="ck_case_risk"),
        CheckConstraint("version >= 0", name="ck_case_version"),
    )


class EvidenceTable(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    evidence_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(512), nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    media_type: Mapped[str] = mapped_column(String(160), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    ingested_by: Mapped[str] = mapped_column(String(128), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    page: Mapped[int | None] = mapped_column(Integer)
    bounding_box: Mapped[list[float] | None] = mapped_column(JSON)

    __table_args__ = (
        UniqueConstraint("case_id", "id", name="uq_evidence_case_id"),
        CheckConstraint("length(content_sha256) = 64", name="ck_evidence_sha256_length"),
        CheckConstraint("content_sha256 = lower(content_sha256)", name="ck_evidence_sha256_lower"),
        CheckConstraint("size_bytes >= 0", name="ck_evidence_size"),
    )


class EntityTable(Base):
    __tablename__ = "entities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(512), nullable=False)
    attributes: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (
        UniqueConstraint("case_id", "id", name="uq_entity_case_id"),
        Index("ix_entity_case_kind", "case_id", "kind"),
    )


class RelationshipTable(Base):
    __tablename__ = "relationships"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    target_entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    attributes: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (
        UniqueConstraint("case_id", "id", name="uq_relationship_case_id"),
        ForeignKeyConstraint(
            ["case_id", "source_entity_id"],
            ["entities.case_id", "entities.id"],
            ondelete="CASCADE",
            name="fk_relationship_source_same_case",
        ),
        ForeignKeyConstraint(
            ["case_id", "target_entity_id"],
            ["entities.case_id", "entities.id"],
            ondelete="CASCADE",
            name="fk_relationship_target_same_case",
        ),
        CheckConstraint("source_entity_id <> target_entity_id", name="ck_relationship_distinct"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_relationship_confidence"),
    )


class RelationshipEvidenceTable(Base):
    __tablename__ = "relationship_evidence"

    case_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    relationship_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    evidence_id: Mapped[str] = mapped_column(String(64), primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["case_id", "relationship_id"],
            ["relationships.case_id", "relationships.id"],
            ondelete="CASCADE",
            name="fk_relationship_evidence_relationship",
        ),
        ForeignKeyConstraint(
            ["case_id", "evidence_id"],
            ["evidence.case_id", "evidence.id"],
            ondelete="RESTRICT",
            name="fk_relationship_evidence_same_case",
        ),
    )


class FindingTable(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="proposed")
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    proposed_by: Mapped[str] = mapped_column(String(128), nullable=False)
    generated_by: Mapped[str] = mapped_column(String(128), nullable=False)
    signature_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    proposed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    reviewed_by: Mapped[str | None] = mapped_column(String(128))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("case_id", "id", name="uq_finding_case_id"),
        UniqueConstraint("case_id", "signature_sha256", name="uq_finding_case_signature"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_finding_confidence"),
        CheckConstraint("length(signature_sha256) = 64", name="ck_finding_signature_length"),
        CheckConstraint(
            "reviewed_by IS NULL OR reviewed_by <> proposed_by",
            name="ck_finding_four_eyes",
        ),
    )


class FindingEvidenceTable(Base):
    __tablename__ = "finding_evidence"

    case_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    finding_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    evidence_id: Mapped[str] = mapped_column(String(64), primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["case_id", "finding_id"],
            ["findings.case_id", "findings.id"],
            ondelete="CASCADE",
            name="fk_finding_evidence_finding",
        ),
        ForeignKeyConstraint(
            ["case_id", "evidence_id"],
            ["evidence.case_id", "evidence.id"],
            ondelete="RESTRICT",
            name="fk_finding_evidence_same_case",
        ),
    )


class ChainOfCustodyTable(Base):
    __tablename__ = "chain_of_custody"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["case_id", "evidence_id"],
            ["evidence.case_id", "evidence.id"],
            ondelete="RESTRICT",
            name="fk_custody_evidence_same_case",
        ),
        Index("ix_custody_evidence_time", "evidence_id", "occurred_at"),
    )


class AuditEventTable(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(96), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    __table_args__ = (
        ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="RESTRICT"),
        Index("ix_audit_case_time", "case_id", "occurred_at"),
    )


class InvestigationRunTable(Base):
    __tablename__ = "investigation_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    requested_by: Mapped[str] = mapped_column(String(128), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(96))


class WorkflowOutboxTable(Base):
    __tablename__ = "workflow_outbox"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    aggregate_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(96), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    leased_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        UniqueConstraint("aggregate_id", "event_type", name="uq_outbox_aggregate_event"),
        CheckConstraint("attempts >= 0", name="ck_outbox_attempts"),
        Index("ix_outbox_dispatch", "status", "available_at"),
    )


def _reject_ledger_mutation(*_: object) -> None:
    raise RuntimeError("tamper-evident ledger rows are append-only")


event.listen(AuditEventTable, "before_update", _reject_ledger_mutation)
event.listen(AuditEventTable, "before_delete", _reject_ledger_mutation)
event.listen(ChainOfCustodyTable, "before_update", _reject_ledger_mutation)
event.listen(ChainOfCustodyTable, "before_delete", _reject_ledger_mutation)

event.listen(
    AuditEventTable.__table__,
    "after_create",
    DDL(  # type: ignore[no-untyped-call]
        """
        CREATE OR REPLACE FUNCTION evidencegraph_reject_ledger_mutation()
        RETURNS trigger AS $fn$
        BEGIN
          RAISE EXCEPTION 'tamper-evident ledger rows are append-only';
        END;
        $fn$ LANGUAGE plpgsql;
        CREATE TRIGGER audit_events_append_only
        BEFORE UPDATE OR DELETE ON audit_events
        FOR EACH ROW EXECUTE FUNCTION evidencegraph_reject_ledger_mutation();
        """
    ).execute_if(dialect="postgresql"),
)
event.listen(
    ChainOfCustodyTable.__table__,
    "after_create",
    DDL(  # type: ignore[no-untyped-call]
        """
        CREATE OR REPLACE FUNCTION evidencegraph_reject_ledger_mutation()
        RETURNS trigger AS $fn$
        BEGIN
          RAISE EXCEPTION 'tamper-evident ledger rows are append-only';
        END;
        $fn$ LANGUAGE plpgsql;
        CREATE TRIGGER chain_of_custody_append_only
        BEFORE UPDATE OR DELETE ON chain_of_custody
        FOR EACH ROW EXECUTE FUNCTION evidencegraph_reject_ledger_mutation();
        """
    ).execute_if(dialect="postgresql"),
)
