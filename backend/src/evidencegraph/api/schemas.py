from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from evidencegraph.domain.models import CaseStatus, EvidenceType, Finding, FindingStatus


class CreateCaseRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=4000)


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    evidence_type: EvidenceType
    source: str
    content_sha256: str
    storage_key: str
    ingested_by: str
    ingested_at: datetime
    page: int | None


class CaseResponse(BaseModel):
    id: str
    title: str
    description: str
    created_by: str
    created_at: datetime
    status: CaseStatus
    evidence_count: int

    @classmethod
    def from_domain(cls, case: object) -> "CaseResponse":
        from evidencegraph.domain.models import InvestigationCase

        if not isinstance(case, InvestigationCase):
            raise TypeError("expected InvestigationCase")
        return cls(
            id=case.id,
            title=case.title,
            description=case.description,
            created_by=case.created_by,
            created_at=case.created_at,
            status=case.status,
            evidence_count=len(case.evidence),
        )


class HealthResponse(BaseModel):
    status: str
    version: str


class FindingResponse(BaseModel):
    id: str
    case_id: str
    title: str
    rationale: str
    evidence_ids: tuple[str, ...]
    status: FindingStatus
    confidence: float
    proposed_by: str
    proposed_at: datetime
    reviewed_by: str | None
    reviewed_at: datetime | None

    @classmethod
    def from_domain(cls, finding: Finding) -> "FindingResponse":
        return cls(
            id=finding.id,
            case_id=finding.case_id,
            title=finding.title,
            rationale=finding.rationale,
            evidence_ids=finding.evidence_ids,
            status=finding.status,
            confidence=finding.confidence,
            proposed_by=finding.proposed_by,
            proposed_at=finding.proposed_at,
            reviewed_by=finding.reviewed_by,
            reviewed_at=finding.reviewed_at,
        )


class ReviewFindingRequest(BaseModel):
    decision: FindingStatus
