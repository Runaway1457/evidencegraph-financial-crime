from evidencegraph.application.ports import AgentFindingProposal
from evidencegraph.domain.models import InvestigationCase


class DeterministicInvestigator:
    """Explainable baseline used for regression tests and offline demos."""

    identity = "deterministic-investigator-v1"

    def propose(self, case: InvestigationCase) -> tuple[AgentFindingProposal, ...]:
        proposals: list[AgentFindingProposal] = []
        seen_paths: set[tuple[str, str]] = set()

        for first in case.relationships:
            for second in case.relationships:
                path_key = (first.id, second.id)
                if first.target_entity_id != second.source_entity_id or path_key in seen_paths:
                    continue
                seen_paths.add(path_key)
                evidence_ids = tuple(
                    dict.fromkeys((*first.evidence_ids, *second.evidence_ids))
                )
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
        return tuple(proposals)
