#!/usr/bin/env python3
from evidencegraph.config import get_settings
from evidencegraph.domain.models import (
    Entity,
    EntityKind,
    Evidence,
    EvidenceType,
    InvestigationCase,
    Relationship,
    utc_now,
)
from evidencegraph.infrastructure.database import build_engine, build_session_factory
from evidencegraph.infrastructure.sqlalchemy_repository import SqlAlchemyCaseRepository


def build_demo_case() -> InvestigationCase:
    case_id = "case_1"
    transfer = Evidence.create(
        case_id=case_id,
        evidence_type=EvidenceType.TRANSACTION,
        source="synthetic://meridian/payments-2026-05.json",
        content_sha256="a" * 64,
        storage_key="synthetic/case_1/payments-2026-05.json",
        ingested_by="seed:verified-demo",
        media_type="application/json",
        size_bytes=2048,
    )
    registry = Evidence.create(
        case_id=case_id,
        evidence_type=EvidenceType.REGISTRY,
        source="synthetic://meridian/company-registry.json",
        content_sha256="b" * 64,
        storage_key="synthetic/case_1/company-registry.json",
        ingested_by="seed:verified-demo",
        media_type="application/json",
        size_bytes=1024,
    )
    source = Entity(
        id="entity_nova_meridian",
        case_id=case_id,
        kind=EntityKind.ORGANIZATION,
        canonical_name="Nova Meridian Holdings",
        attributes={"jurisdiction": "GB", "risk": "high"},
    )
    intermediary = Entity(
        id="entity_orion_trade",
        case_id=case_id,
        kind=EntityKind.ORGANIZATION,
        canonical_name="Orion Trade FZE",
        attributes={"jurisdiction": "AE", "risk": "elevated"},
    )
    destination = Entity(
        id="entity_wallet_7a91f",
        case_id=case_id,
        kind=EntityKind.WALLET,
        canonical_name="0x7A91F",
        attributes={"network": "synthetic-chain", "risk": "high"},
    )
    first = Relationship(
        id="relationship_transfer_1",
        case_id=case_id,
        source_entity_id=source.id,
        target_entity_id=intermediary.id,
        relationship_type="transferred_to",
        evidence_ids=(transfer.id, registry.id),
        confidence=0.94,
    )
    second = Relationship(
        id="relationship_transfer_2",
        case_id=case_id,
        source_entity_id=intermediary.id,
        target_entity_id=destination.id,
        relationship_type="transferred_to",
        evidence_ids=(transfer.id,),
        confidence=0.92,
    )
    return InvestigationCase(
        id=case_id,
        title="Project Meridian",
        description="Synthetic cross-border layering investigation for the verified demo.",
        created_by="seed:verified-demo",
        created_at=utc_now(),
        evidence=(transfer, registry),
        entities=(source, intermediary, destination),
        relationships=(first, second),
    )


def main() -> None:
    settings = get_settings()
    engine = build_engine(settings)
    repository = SqlAlchemyCaseRepository(build_session_factory(engine))
    if repository.get("case_1") is None:
        repository.save(build_demo_case())
        print("seeded case_1")
    else:
        print("case_1 already present")


if __name__ == "__main__":
    main()
