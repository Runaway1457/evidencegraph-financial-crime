from dataclasses import replace

from evidencegraph.application.grounding import validate_agent_proposals
from evidencegraph.application.ports import (
    CaseRepository,
    InvestigatorAgent,
    PolicyPort,
)
from evidencegraph.domain.errors import AuthorizationDeniedError, NotFoundError
from evidencegraph.domain.hashing import sha256_bytes
from evidencegraph.domain.models import (
    Evidence,
    EvidenceType,
    Finding,
    FindingStatus,
    InvestigationCase,
    new_id,
    utc_now,
)


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


class InvestigationService:
    """Orchestrates governed AI output without granting the model write access."""

    def __init__(
        self,
        repository: CaseRepository,
        agent: InvestigatorAgent,
        policy: PolicyPort,
    ) -> None:
        self._repository = repository
        self._agent = agent
        self._policy = policy

    def run(self, *, case_id: str, actor_id: str) -> tuple[Finding, ...]:
        case = self._get_case(case_id)
        decision = self._policy.authorize(
            actor_id=actor_id,
            action="investigation.run",
            case_id=case_id,
        )
        if not decision.allowed:
            raise AuthorizationDeniedError(decision.reason or "policy denied investigation")

        proposals = self._agent.propose(case)
        validate_agent_proposals(case, proposals)

        existing_signatures = {
            (finding.title, finding.rationale, finding.evidence_ids) for finding in case.findings
        }
        staged = case
        created: list[Finding] = []
        for proposal in proposals:
            signature = (proposal.title.strip(), proposal.rationale.strip(), proposal.evidence_ids)
            if signature in existing_signatures:
                continue
            finding = Finding(
                id=new_id("finding"),
                case_id=case.id,
                title=signature[0],
                rationale=signature[1],
                evidence_ids=proposal.evidence_ids,
                status=FindingStatus.PROPOSED,
                confidence=proposal.confidence,
                proposed_by=self._agent.identity,
                proposed_at=utc_now(),
            )
            staged = staged.add_finding(finding)
            created.append(finding)
            existing_signatures.add(signature)

        if created:
            self._repository.save(staged)
        return tuple(created)

    def review(
        self,
        *,
        case_id: str,
        finding_id: str,
        reviewer_id: str,
        decision: FindingStatus,
    ) -> Finding:
        case = self._get_case(case_id)
        policy_decision = self._policy.authorize(
            actor_id=reviewer_id,
            action="finding.review",
            case_id=case_id,
        )
        if not policy_decision.allowed:
            raise AuthorizationDeniedError(policy_decision.reason or "policy denied review")

        finding = next((item for item in case.findings if item.id == finding_id), None)
        if finding is None:
            raise NotFoundError("finding was not found")
        reviewed = finding.review(reviewer_id=reviewer_id, decision=decision)
        findings = tuple(reviewed if item.id == finding_id else item for item in case.findings)
        self._repository.save(replace(case, findings=findings))
        return reviewed

    def _get_case(self, case_id: str) -> InvestigationCase:
        case = self._repository.get(case_id)
        if case is None:
            raise NotFoundError(f"case {case_id!r} was not found")
        return case
