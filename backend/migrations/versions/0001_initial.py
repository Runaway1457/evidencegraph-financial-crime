"""Create the immutable evidence-first relational schema.

Revision ID: 0001
Revises:
Create Date: 2026-09-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cases",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("risk_score BETWEEN 0 AND 100", name="ck_case_risk"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "evidence",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("case_id", sa.String(length=64), nullable=False),
        sa.Column("evidence_type", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=512), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=1024), nullable=False),
        sa.Column("media_type", sa.String(length=160), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("ingested_by", sa.String(length=128), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("bounding_box", sa.JSON(), nullable=True),
        sa.CheckConstraint("length(content_sha256) = 64", name="ck_evidence_sha256_length"),
        sa.CheckConstraint("size_bytes >= 0", name="ck_evidence_size"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "id", name="uq_evidence_case_id"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_table(
        "entities",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("case_id", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("canonical_name", sa.String(length=512), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "id", name="uq_entity_case_id"),
    )
    op.create_index("ix_entity_case_kind", "entities", ["case_id", "kind"], unique=False)
    op.create_table(
        "relationships",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("case_id", sa.String(length=64), nullable=False),
        sa.Column("source_entity_id", sa.String(length=64), nullable=False),
        sa.Column("target_entity_id", sa.String(length=64), nullable=False),
        sa.Column("relationship_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_relationship_confidence"),
        sa.CheckConstraint("source_entity_id <> target_entity_id", name="ck_relationship_distinct"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["case_id", "source_entity_id"],
            ["entities.case_id", "entities.id"],
            name="fk_relationship_source_same_case",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["case_id", "target_entity_id"],
            ["entities.case_id", "entities.id"],
            name="fk_relationship_target_same_case",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "id", name="uq_relationship_case_id"),
    )
    op.create_table(
        "findings",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("case_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("proposed_by", sa.String(length=128), nullable=False),
        sa.Column("proposed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_by", sa.String(length=128), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_finding_confidence"),
        sa.CheckConstraint(
            "reviewed_by IS NULL OR reviewed_by <> proposed_by",
            name="ck_finding_four_eyes",
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "id", name="uq_finding_case_id"),
    )
    op.create_table(
        "relationship_evidence",
        sa.Column("case_id", sa.String(length=64), nullable=False),
        sa.Column("relationship_id", sa.String(length=64), nullable=False),
        sa.Column("evidence_id", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["case_id", "evidence_id"],
            ["evidence.case_id", "evidence.id"],
            name="fk_relationship_evidence_same_case",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["case_id", "relationship_id"],
            ["relationships.case_id", "relationships.id"],
            name="fk_relationship_evidence_relationship",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("case_id", "relationship_id", "evidence_id"),
    )
    op.create_table(
        "finding_evidence",
        sa.Column("case_id", sa.String(length=64), nullable=False),
        sa.Column("finding_id", sa.String(length=64), nullable=False),
        sa.Column("evidence_id", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["case_id", "evidence_id"],
            ["evidence.case_id", "evidence.id"],
            name="fk_finding_evidence_same_case",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["case_id", "finding_id"],
            ["findings.case_id", "findings.id"],
            name="fk_finding_evidence_finding",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("case_id", "finding_id", "evidence_id"),
    )
    op.create_table(
        "chain_of_custody",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("case_id", sa.String(length=64), nullable=False),
        sa.Column("evidence_id", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("previous_hash", sa.String(length=64), nullable=False),
        sa.Column("event_hash", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["case_id", "evidence_id"],
            ["evidence.case_id", "evidence.id"],
            name="fk_custody_evidence_same_case",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_hash"),
    )
    op.create_index(
        "ix_custody_evidence_time",
        "chain_of_custody",
        ["evidence_id", "occurred_at"],
        unique=False,
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("case_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=96), nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("previous_hash", sa.String(length=64), nullable=False),
        sa.Column("event_hash", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_hash"),
    )
    op.create_index("ix_audit_case_time", "audit_events", ["case_id", "occurred_at"], unique=False)
    op.create_table(
        "investigation_runs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("case_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("requested_by", sa.String(length=128), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=96), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "workflow_outbox",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("aggregate_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=96), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("leased_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("attempts >= 0", name="ck_outbox_attempts"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("aggregate_id", "event_type", name="uq_outbox_aggregate_event"),
    )
    op.create_index(
        "ix_outbox_dispatch",
        "workflow_outbox",
        ["status", "available_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_dispatch", table_name="workflow_outbox")
    op.drop_table("workflow_outbox")
    op.drop_table("investigation_runs")
    op.drop_index("ix_audit_case_time", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_custody_evidence_time", table_name="chain_of_custody")
    op.drop_table("chain_of_custody")
    op.drop_table("finding_evidence")
    op.drop_table("relationship_evidence")
    op.drop_table("findings")
    op.drop_table("relationships")
    op.drop_index("ix_entity_case_kind", table_name="entities")
    op.drop_table("entities")
    op.drop_table("evidence")
    op.drop_table("cases")
