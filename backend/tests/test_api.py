from fastapi.testclient import TestClient

from evidencegraph.api.main import create_app
from evidencegraph.config import Settings
from evidencegraph.domain.models import (
    Entity,
    EntityKind,
    Evidence,
    EvidenceType,
    InvestigationCase,
    Relationship,
    utc_now,
)
from evidencegraph.infrastructure.memory import InMemoryCaseRepository
from evidencegraph.infrastructure.object_store import InMemoryObjectStore

repository = InMemoryCaseRepository()
object_store = InMemoryObjectStore()
app = create_app(
    settings_override=Settings(environment="test", max_upload_bytes=16),
    repository_override=repository,
    object_store_override=object_store,
)
client = TestClient(app)


def setup_function() -> None:
    repository._cases.clear()
    object_store.objects.clear()


def test_health_and_readiness() -> None:
    live = client.get("/health/live")
    ready = client.get("/health/ready")
    assert live.status_code == 200
    assert live.json()["status"] == "ok"
    assert live.headers["X-Request-ID"]
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"


def test_create_and_get_case() -> None:
    created = client.post(
        "/api/v1/cases",
        headers={"X-Actor-ID": "analyst_1"},
        json={"title": "Project Meridian", "description": "Synthetic investigation"},
    )
    assert created.status_code == 201

    case_id = created.json()["id"]
    fetched = client.get(f"/api/v1/cases/{case_id}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Project Meridian"


def test_unknown_case_does_not_leak_details() -> None:
    response = client.get("/api/v1/cases/not-real")
    assert response.status_code == 404
    assert response.json() == {"detail": "case not found"}


def test_binary_evidence_ingestion_is_bounded_stored_and_ledgered() -> None:
    created = client.post(
        "/api/v1/cases",
        headers={"X-Actor-ID": "analyst_1"},
        json={"title": "Project Meridian", "description": "Synthetic investigation"},
    )
    case_id = created.json()["id"]

    response = client.post(
        f"/api/v1/cases/{case_id}/evidence",
        params={"evidence_type": "document", "source": "analyst upload"},
        headers={"X-Actor-ID": "analyst_1", "Content-Type": "application/pdf"},
        content=b"verified bytes",
    )

    assert response.status_code == 201
    assert response.json()["size_bytes"] == 14
    assert object_store.objects[response.json()["storage_key"]] == b"verified bytes"
    assert repository.get(case_id).evidence[0].id == response.json()["id"]


def test_binary_evidence_ingestion_rejects_oversized_payload() -> None:
    created = client.post(
        "/api/v1/cases",
        json={"title": "Project Meridian", "description": ""},
    )
    response = client.post(
        f"/api/v1/cases/{created.json()['id']}/evidence",
        params={"evidence_type": "document", "source": "upload"},
        content=b"x" * 17,
    )
    assert response.status_code == 413
    assert object_store.objects == {}


def _seed_grounded_case() -> InvestigationCase:
    evidence = Evidence.create(
        case_id="case_1",
        evidence_type=EvidenceType.TRANSACTION,
        source="synthetic",
        content_sha256="a" * 64,
        storage_key="synthetic/case_1/transfer.json",
        ingested_by="seed",
    )
    source = Entity(
        id="source",
        case_id="case_1",
        kind=EntityKind.ORGANIZATION,
        canonical_name="Nova Meridian",
    )
    middle = Entity(
        id="middle",
        case_id="case_1",
        kind=EntityKind.ORGANIZATION,
        canonical_name="Orion Trade",
    )
    target = Entity(
        id="target",
        case_id="case_1",
        kind=EntityKind.WALLET,
        canonical_name="0x7A91F",
    )
    relationships = (
        Relationship(
            id="r1",
            case_id="case_1",
            source_entity_id=source.id,
            target_entity_id=middle.id,
            relationship_type="transferred_to",
            evidence_ids=(evidence.id,),
            confidence=0.94,
        ),
        Relationship(
            id="r2",
            case_id="case_1",
            source_entity_id=middle.id,
            target_entity_id=target.id,
            relationship_type="transferred_to",
            evidence_ids=(evidence.id,),
            confidence=0.92,
        ),
    )
    return InvestigationCase(
        id="case_1",
        title="Project Meridian",
        description="Synthetic",
        created_by="seed",
        created_at=utc_now(),
        evidence=(evidence,),
        entities=(source, middle, target),
        relationships=relationships,
    )


def test_governed_investigate_review_and_list_flow() -> None:
    repository.save(_seed_grounded_case())

    investigation = client.post(
        "/api/v1/cases/case_1/investigations",
        headers={"X-Actor-ID": "analyst_1"},
    )
    assert investigation.status_code == 202
    assert investigation.json()["status"] == "queued"
    run_id = investigation.json()["id"]
    assert client.get(f"/api/v1/investigation-runs/{run_id}").json()["status"] == "queued"

    finding = app.state.investigation_service.run(case_id="case_1", actor_id="analyst_1")[0]
    finding_id = finding.id

    self_review = client.post(
        f"/api/v1/cases/case_1/findings/{finding_id}/review",
        headers={"X-Actor-ID": "analyst_1"},
        json={"decision": "confirmed"},
    )
    assert self_review.status_code == 422

    reviewed = client.post(
        f"/api/v1/cases/case_1/findings/{finding_id}/review",
        headers={"X-Actor-ID": "reviewer_2"},
        json={"decision": "confirmed"},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "confirmed"
    assert reviewed.json()["reviewed_by"] == "reviewer_2"

    listed = client.get("/api/v1/cases/case_1/findings")
    assert listed.status_code == 200
    assert listed.json()[0]["status"] == "confirmed"
