from typing import Final

import httpx

from evidencegraph.application.ports import PolicyDecision


class DevelopmentPolicy:
    """Local policy with the same contract as the production OPA adapter."""

    def authorize(self, *, actor_id: str, action: str, case_id: str) -> PolicyDecision:
        if not actor_id or not case_id:
            return PolicyDecision(allowed=False, reason="actor and case identity are required")
        return PolicyDecision(
            allowed=True,
            reason="development policy",
            obligations=("append_audit_event",) if action == "investigation.run" else (),
        )


class OpaPolicyClient:
    """Fail-closed adapter for an OPA data API decision document."""

    _UNAVAILABLE: Final = "policy service unavailable"

    def __init__(
        self,
        *,
        base_url: str,
        decision_path: str = "evidencegraph/authorize",
        timeout_seconds: float = 2.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._url = f"{base_url.rstrip('/')}/v1/data/{decision_path.strip('/')}"
        self._client = client or httpx.Client(timeout=timeout_seconds)
        self._owns_client = client is None

    def authorize(self, *, actor_id: str, action: str, case_id: str) -> PolicyDecision:
        try:
            response = self._client.post(
                self._url,
                json={"input": {"actor_id": actor_id, "action": action, "case_id": case_id}},
            )
            response.raise_for_status()
            document = response.json()
        except (httpx.HTTPError, ValueError):
            return PolicyDecision(allowed=False, reason=self._UNAVAILABLE)

        result = document.get("result") if isinstance(document, dict) else None
        if not isinstance(result, dict) or result.get("allow") is not True:
            reason = result.get("reason") if isinstance(result, dict) else None
            return PolicyDecision(
                allowed=False,
                reason=reason if isinstance(reason, str) else "policy denied action",
            )

        obligations = result.get("obligations", [])
        safe_obligations = (
            tuple(item for item in obligations if isinstance(item, str))
            if isinstance(obligations, list)
            else ()
        )
        reason = result.get("reason")
        return PolicyDecision(
            allowed=True,
            reason=reason if isinstance(reason, str) else "policy allowed action",
            obligations=safe_obligations,
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
