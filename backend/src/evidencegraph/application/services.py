from dataclasses import replace

from evidencegraph.application.ports import (
    AgentFindingProposal,
    CaseRepository,
    InvestigatorAgent,
    ObjectStore,
    PolicyPort,
)
from evidencegraph.domain.errors import AuthorizationDeniedError, DomainError, NotFoundError
from evidencegraph.domain.hashing import sha256_bytes
from evidencegraph.domain.models import (
    CaseSummary,
    Evidence,
    EvidenceType,
    Finding,
    FindingStatus,
    InvestigationCase,
    new_id,
    utc_now,
)


class CaseService:
    def __init__(self, repository: CaseRepository, object_store: ObjectStore | None = None) -> None:
        self._repository = repository
        self._object_store = object_store

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

    def list_cases(self, *, limit: int = 50, offset: int = 0) -> tuple[CaseSummary, ...]:
        return self._repository.list_summaries(limit=limit, offset=offset)

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
        if self._object_store is not None:
            self._object_store.put(storage_key, content)
        try:
            self._repository.save(case.add_evidence(evidence))
        except Exception:
            if self._object_store is not None:
                self._object_store.delete(storage_key)
            raise
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
        self.authorize_run(case_id=case_id, actor_id=actor_id)

        proposals = self._agent.propose(case)
        self._validate_proposals(case, proposals)

        existing_signatures = {finding.signature_sha256 for finding in case.findings}
        created: list[Finding] = []
        for proposal in proposals:
            finding = Finding(
                id=new_id("finding"),
                case_id=case.id,
                title=proposal.title.strip(),
                rationale=proposal.rationale.strip(),
                evidence_ids=proposal.evidence_ids,
                status=FindingStatus.PROPOSED,
                confidence=proposal.confidence,
                proposed_by=actor_id,
                generated_by=self._agent.identity,
                proposed_at=utc_now(),
            )
            if finding.signature_sha256 in existing_signatures:
                continue
            created.append(finding)
            existing_signatures.add(finding.signature_sha256)

        if created:
            self._repository.save(
                replace(
                    case,
                    findings=(*case.findings, *created),
                    version=case.version + 1,
                )
            )
        return tuple(created)

    def authorize_run(self, *, case_id: str, actor_id: str) -> None:
        self._get_case(case_id)
        decision = self._policy.authorize(
            actor_id=actor_id,
            action="investigation.run",
            case_id=case_id,
        )
        if not decision.allowed:
            raise AuthorizationDeniedError(decision.reason or "policy denied investigation")

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
        self._repository.save(replace(case, findings=findings, version=case.version + 1))
        return reviewed

    def _get_case(self, case_id: str) -> InvestigationCase:
        case = self._repository.get(case_id)
        if case is None:
            raise NotFoundError(f"case {case_id!r} was not found")
        return case

    @staticmethod
    def _validate_proposals(
        case: InvestigationCase,
        proposals: tuple[AgentFindingProposal, ...],
    ) -> None:
        known_evidence = {item.id for item in case.evidence}
        for proposal in proposals:
            if not proposal.title.strip() or not proposal.rationale.strip():
                raise DomainError("agent proposals require title and rationale")
            if not proposal.evidence_ids:
                raise DomainError("agent proposals must cite evidence")
            if missing := set(proposal.evidence_ids) - known_evidence:
                raise DomainError(f"agent cited unknown evidence: {sorted(missing)}")
            if not 0.0 <= proposal.confidence <= 1.0:
                raise DomainError("agent confidence must be between 0 and 1")
