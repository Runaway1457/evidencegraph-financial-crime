from dataclasses import replace

import pytest

from evidencegraph.domain.audit import GENESIS_HASH, AuditChain, AuditEvent
from evidencegraph.domain.errors import DomainError


def test_audit_chain_links_and_verifies_events() -> None:
    chain = AuditChain()
    first = chain.append(
        case_id="case_1",
        event_type="case.created",
        actor_id="analyst_1",
        payload={"title": "Meridian"},
    )
    second = chain.append(
        case_id="case_1",
        event_type="evidence.ingested",
        actor_id="analyst_1",
        payload={"evidence_id": "ev_1"},
    )

    assert first.previous_hash == GENESIS_HASH
    assert second.previous_hash == first.event_hash
    assert chain.events == (first, second)
    assert chain.verify()


def test_audit_chain_detects_payload_tampering() -> None:
    chain = AuditChain()
    event = chain.append(
        case_id="case_1",
        event_type="finding.proposed",
        actor_id="agent_1",
        payload={"finding_id": "finding_1"},
    )
    chain._events[0] = replace(event, payload={"finding_id": "tampered"})

    assert not chain.verify()


def test_audit_event_rejects_incomplete_identity_and_bad_parent_hash() -> None:
    with pytest.raises(DomainError, match="required"):
        AuditEvent.create(case_id="", event_type="case.created", actor_id="a1", payload={})
    with pytest.raises(DomainError, match="previous_hash"):
        AuditEvent.create(
            case_id="case_1",
            event_type="case.created",
            actor_id="a1",
            payload={},
            previous_hash="bad",
        )
