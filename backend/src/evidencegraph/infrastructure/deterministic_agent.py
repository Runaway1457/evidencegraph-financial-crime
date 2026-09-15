from evidencegraph.application.ports import AgentFindingProposal
from evidencegraph.domain.models import InvestigationCase, Relationship


class DeterministicInvestigator:
    """Explainable baseline used for regression tests and offline demos."""

    identity = "deterministic-investigator-v1"

    def __init__(self, *, max_proposals: int = 50) -> None:
        if max_proposals < 1:
            raise ValueError("max_proposals must be positive")
        self._max_proposals = max_proposals

    def propose(self, case: InvestigationCase) -> tuple[AgentFindingProposal, ...]:
        proposals: list[AgentFindingProposal] = []
        by_source: dict[str, list[Relationship]] = {}
        for relationship in case.relationships:
            by_source.setdefault(relationship.source_entity_id, []).append(relationship)

        for first in case.relationships:
            for second in by_source.get(first.target_entity_id, ()):
                if second.target_entity_id == first.source_entity_id:
                    continue
                evidence_ids = tuple(dict.fromkeys((*first.evidence_ids, *second.evidence_ids)))
                proposals.append(
                    AgentFindingProposal(
                        title="Multi-hop transfer path for review",
                        rationale=(
                            f"Evidence-backed relationships {first.id} and {second.id} "
                            "form a two-hop path. The pattern requires independent review."
                        ),
                        evidence_ids=evidence_ids,
                        confidence=min(first.confidence, second.confidence),
                    )
                )
                if len(proposals) >= self._max_proposals:
                    return tuple(proposals)
        return tuple(proposals)
