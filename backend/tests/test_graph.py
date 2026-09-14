import pytest

from evidencegraph.domain.errors import DomainError
from evidencegraph.domain.graph import EvidenceGraph, GraphEdge


def edge(
    edge_id: str,
    source: str,
    target: str,
    evidence_ids: tuple[str, ...],
    *,
    case_id: str = "case_1",
) -> GraphEdge:
    return GraphEdge(
        id=edge_id,
        case_id=case_id,
        source_id=source,
        target_id=target,
        relationship_type="transferred_to",
        evidence_ids=evidence_ids,
        confidence=0.92,
    )


def test_multi_hop_path_preserves_order_and_deduplicates_citations() -> None:
    graph = EvidenceGraph("case_1")
    graph.add_edge(edge("r1", "company_a", "company_b", ("ev_1", "ev_2")))
    graph.add_edge(edge("r2", "company_b", "wallet_c", ("ev_2", "ev_3")))

    path = graph.shortest_path(source_id="company_a", target_id="wallet_c", max_hops=3)

    assert path is not None
    assert tuple(item.id for item in path.edges) == ("r1", "r2")
    assert path.evidence_ids == ("ev_1", "ev_2", "ev_3")


def test_graph_returns_none_when_target_is_unreachable_or_depth_is_insufficient() -> None:
    graph = EvidenceGraph("case_1")
    graph.add_edge(edge("r1", "a", "b", ("ev_1",)))
    graph.add_edge(edge("r2", "b", "c", ("ev_2",)))

    assert graph.shortest_path(source_id="a", target_id="c", max_hops=1) is None
    assert graph.shortest_path(source_id="a", target_id="missing", max_hops=3) is None


def test_graph_handles_zero_length_path() -> None:
    graph = EvidenceGraph("case_1")
    path = graph.shortest_path(source_id="a", target_id="a")
    assert path is not None
    assert path.edges == ()


def test_graph_rejects_ungrounded_cross_case_and_duplicate_edges() -> None:
    with pytest.raises(DomainError, match="citations"):
        edge("r1", "a", "b", ())

    graph = EvidenceGraph("case_1")
    with pytest.raises(DomainError, match="another case"):
        graph.add_edge(edge("foreign", "a", "b", ("ev_1",), case_id="case_2"))

    graph.add_edge(edge("r1", "a", "b", ("ev_1",)))
    with pytest.raises(DomainError, match="already exists"):
        graph.add_edge(edge("r1", "a", "c", ("ev_2",)))

    with pytest.raises(DomainError, match="positive"):
        graph.shortest_path(source_id="a", target_id="b", max_hops=0)
