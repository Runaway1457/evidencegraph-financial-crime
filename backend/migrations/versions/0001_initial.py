"""Create the evidence-first transactional schema.

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
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("risk_score BETWEEN 0 AND 100", name="ck_case_risk"),
        sa.CheckConstraint("version >= 0", name="ck_case_version"),
    )
    op.create_table(
        "evidence",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("evidence_type", sa.String(32), nullable=False),
        sa.Column("source", sa.String(512), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("storage_key", sa.String(1024), nullable=False),
        sa.Column("media_type", sa.String(160), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("ingested_by", sa.String(128), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("page", sa.Integer()),
        sa.Column("bounding_box", sa.JSON()),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("case_id", "id", name="uq_evidence_case_id"),
        sa.UniqueConstraint("storage_key"),
        sa.CheckConstraint("length(content_sha256) = 64", name="ck_evidence_sha256_length"),
        sa.CheckConstraint(
            "content_sha256 = lower(content_sha256)", name="ck_evidence_sha256_lower"
        ),
        sa.CheckConstraint("size_bytes >= 0", name="ck_evidence_size"),
    )
    op.create_table(
        "entities",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("canonical_name", sa.String(512), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("case_id", "id", name="uq_entity_case_id"),
    )
    op.create_index("ix_entity_case_kind", "entities", ["case_id", "kind"])
    op.create_table(
        "relationships",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("source_entity_id", sa.String(64), nullable=False),
        sa.Column("target_entity_id", sa.String(64), nullable=False),
        sa.Column("relationship_type", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
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
        sa.UniqueConstraint("case_id", "id", name="uq_relationship_case_id"),
        sa.CheckConstraint("source_entity_id <> target_entity_id", name="ck_relationship_distinct"),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_relationship_confidence"),
    )
    op.create_table(
        "relationship_evidence",
        sa.Column("case_id", sa.String(64), primary_key=True),
        sa.Column("relationship_id", sa.String(64), primary_key=True),
        sa.Column("evidence_id", sa.String(64), primary_key=True),
        sa.ForeignKeyConstraint(
            ["case_id", "relationship_id"],
            ["relationships.case_id", "relationships.id"],
            name="fk_relationship_evidence_relationship",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["case_id", "evidence_id"],
            ["evidence.case_id", "evidence.id"],
            name="fk_relationship_evidence_same_case",
            ondelete="RESTRICT",
        ),
    )
    op.create_table(
        "findings",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("proposed_by", sa.String(128), nullable=False),
        sa.Column("generated_by", sa.String(128), nullable=False),
        sa.Column("signature_sha256", sa.String(64), nullable=False),
        sa.Column("proposed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_by", sa.String(128)),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("case_id", "id", name="uq_finding_case_id"),
        sa.UniqueConstraint("case_id", "signature_sha256", name="uq_finding_case_signature"),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_finding_confidence"),
        sa.CheckConstraint("length(signature_sha256) = 64", name="ck_finding_signature_length"),
        sa.CheckConstraint(
            "reviewed_by IS NULL OR reviewed_by <> proposed_by",
            name="ck_finding_four_eyes",
        ),
    )
    op.create_table(
        "finding_evidence",
        sa.Column("case_id", sa.String(64), primary_key=True),
        sa.Column("finding_id", sa.String(64), primary_key=True),
        sa.Column("evidence_id", sa.String(64), primary_key=True),
        sa.ForeignKeyConstraint(
            ["case_id", "finding_id"],
            ["findings.case_id", "findings.id"],
            name="fk_finding_evidence_finding",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["case_id", "evidence_id"],
            ["evidence.case_id", "evidence.id"],
            name="fk_finding_evidence_same_case",
            ondelete="RESTRICT",
        ),
    )
    op.create_table(
        "chain_of_custody",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("evidence_id", sa.String(64), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("actor_id", sa.String(128), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("previous_hash", sa.String(64), nullable=False),
        sa.Column("event_hash", sa.String(64), nullable=False, unique=True),
        sa.ForeignKeyConstraint(
            ["case_id", "evidence_id"],
            ["evidence.case_id", "evidence.id"],
            name="fk_custody_evidence_same_case",
            ondelete="RESTRICT",
        ),
    )
    op.create_index("ix_custody_evidence_time", "chain_of_custody", ["evidence_id", "occurred_at"])
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(96), nullable=False),
        sa.Column("actor_id", sa.String(128), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("previous_hash", sa.String(64), nullable=False),
        sa.Column("event_hash", sa.String(64), nullable=False, unique=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_audit_case_time", "audit_events", ["case_id", "occurred_at"])
    op.create_table(
        "investigation_runs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("requested_by", sa.String(128), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("error_code", sa.String(96)),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "workflow_outbox",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("aggregate_id", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(96), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("leased_until", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text()),
        sa.Column("dispatched_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("aggregate_id", "event_type", name="uq_outbox_aggregate_event"),
        sa.CheckConstraint("attempts >= 0", name="ck_outbox_attempts"),
    )
    op.create_index("ix_outbox_dispatch", "workflow_outbox", ["status", "available_at"])

    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            """
            CREATE OR REPLACE FUNCTION evidencegraph_reject_ledger_mutation()
            RETURNS trigger AS $fn$
            BEGIN
              RAISE EXCEPTION 'tamper-evident ledger rows are append-only';
            END;
            $fn$ LANGUAGE plpgsql
            """
        )
        op.execute(
            """
            CREATE TRIGGER audit_events_append_only
            BEFORE UPDATE OR DELETE ON audit_events
            FOR EACH ROW EXECUTE FUNCTION evidencegraph_reject_ledger_mutation()
            """
        )
        op.execute(
            """
            CREATE TRIGGER chain_of_custody_append_only
            BEFORE UPDATE OR DELETE ON chain_of_custody
            FOR EACH ROW EXECUTE FUNCTION evidencegraph_reject_ledger_mutation()
            """
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
    op.drop_table("findings")
    op.drop_table("relationship_evidence")
    op.drop_table("relationships")
    op.drop_index("ix_entity_case_kind", table_name="entities")
    op.drop_table("entities")
    op.drop_table("evidence")
    op.drop_table("cases")
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP FUNCTION IF EXISTS evidencegraph_reject_ledger_mutation()")
