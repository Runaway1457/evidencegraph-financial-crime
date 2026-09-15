import httpx

from evidencegraph.infrastructure.policy import DevelopmentPolicy, OpaPolicyClient


def client_with(response: httpx.Response) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(lambda request: response))


def test_opa_allow_decision_preserves_obligations() -> None:
    policy = OpaPolicyClient(
        base_url="http://opa:8181",
        client=client_with(
            httpx.Response(
                200,
                json={
                    "result": {
                        "allow": True,
                        "reason": "case assignment verified",
                        "obligations": ["append_audit_event", "mask_pii"],
                    }
                },
            )
        ),
    )

    decision = policy.authorize(
        actor_id="analyst_1",
        action="investigation.run",
        case_id="case_1",
    )
    assert decision.allowed
    assert decision.obligations == ("append_audit_event", "mask_pii")


def test_opa_denial_and_malformed_documents_fail_closed() -> None:
    denied = OpaPolicyClient(
        base_url="http://opa:8181",
        client=client_with(
            httpx.Response(200, json={"result": {"allow": False, "reason": "denied"}})
        ),
    )
    malformed = OpaPolicyClient(
        base_url="http://opa:8181",
        client=client_with(httpx.Response(200, json={"unexpected": True})),
    )

    assert not denied.authorize(actor_id="a", action="x", case_id="c").allowed
    assert not malformed.authorize(actor_id="a", action="x", case_id="c").allowed


def test_opa_transport_failure_is_a_denial() -> None:
    def unavailable(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    policy = OpaPolicyClient(
        base_url="http://opa:8181",
        client=httpx.Client(transport=httpx.MockTransport(unavailable)),
    )
    decision = policy.authorize(actor_id="a", action="x", case_id="c")
    assert not decision.allowed
    assert decision.reason == "policy service unavailable"


def test_development_policy_still_requires_identity() -> None:
    policy = DevelopmentPolicy()
    assert not policy.authorize(actor_id="", action="x", case_id="case_1").allowed
    assert policy.authorize(actor_id="a", action="investigation.run", case_id="case_1").allowed
