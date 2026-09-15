from collections import defaultdict, deque
from dataclasses import dataclass

from evidencegraph.domain.errors import DomainError


@dataclass(frozen=True, slots=True)
class GraphEdge:
    id: str
    case_id: str
    source_id: str
    target_id: str
    relationship_type: str
    evidence_ids: tuple[str, ...]
    confidence: float

    def __post_init__(self) -> None:
        if not self.evidence_ids:
            raise DomainError("graph edges require evidence citations")
        if not 0.0 <= self.confidence <= 1.0:
            raise DomainError("edge confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class EvidencePath:
    edges: tuple[GraphEdge, ...]

    @property
    def evidence_ids(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(item for edge in self.edges for item in edge.evidence_ids))


class EvidenceGraph:
    def __init__(self, case_id: str) -> None:
        if not case_id:
            raise DomainError("case_id is required")
        self.case_id = case_id
        self._adjacency: dict[str, list[GraphEdge]] = defaultdict(list)
        self._edge_ids: set[str] = set()

    def add_edge(self, edge: GraphEdge) -> None:
        if edge.case_id != self.case_id:
            raise DomainError("edge belongs to another case")
        if edge.id in self._edge_ids:
            raise DomainError("edge id already exists")
        self._edge_ids.add(edge.id)
        self._adjacency[edge.source_id].append(edge)

    def shortest_path(
        self,
        *,
        source_id: str,
        target_id: str,
        max_hops: int = 4,
    ) -> EvidencePath | None:
        if max_hops < 1:
            raise DomainError("max_hops must be positive")
        if source_id == target_id:
            return EvidencePath(edges=())

        queue: deque[tuple[str, tuple[GraphEdge, ...], frozenset[str]]] = deque(
            [(source_id, (), frozenset({source_id}))]
        )
        while queue:
            node_id, path, visited = queue.popleft()
            if len(path) >= max_hops:
                continue
            for edge in self._adjacency.get(node_id, ()):
                next_path = (*path, edge)
                if edge.target_id == target_id:
                    return EvidencePath(edges=next_path)
                if edge.target_id not in visited:
                    queue.append((edge.target_id, next_path, visited | {edge.target_id}))
        return None
