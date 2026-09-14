from evidencegraph.application.ports import CaseRepository
from evidencegraph.domain.errors import NotFoundError
from evidencegraph.domain.hashing import sha256_bytes
from evidencegraph.domain.models import Evidence, EvidenceType, InvestigationCase


class CaseService:
    def __init__(self, repository: CaseRepository) -> None:
        self._repository = repository

    def create_case(self, *, title: str, description: str, actor_id: str) -> InvestigationCase:
        case = InvestigationCase.create(
            title=title,
            description=description,
            created_by=actor_id,
        )
        self._repository.save(case)
        return case

    def get_case(self, case_id: str) -> InvestigationCase:
        case = self._repository.get(case_id)
        if case is None:
            raise NotFoundError(f"case {case_id!r} was not found")
        return case

    def list_cases(self) -> tuple[InvestigationCase, ...]:
        return self._repository.list()

    def ingest_evidence(
        self,
        *,
        case_id: str,
        content: bytes,
        evidence_type: EvidenceType,
        source: str,
        storage_key: str,
        actor_id: str,
        media_type: str = "application/octet-stream",
        page: int | None = None,
        bounding_box: tuple[float, float, float, float] | None = None,
    ) -> Evidence:
        case = self.get_case(case_id)
        evidence = Evidence.create(
            case_id=case_id,
            evidence_type=evidence_type,
            source=source,
            content_sha256=sha256_bytes(content),
            storage_key=storage_key,
            ingested_by=actor_id,
            media_type=media_type,
            size_bytes=len(content),
            page=page,
            bounding_box=bounding_box,
        )
        self._repository.save(case.add_evidence(evidence))
        return evidence
