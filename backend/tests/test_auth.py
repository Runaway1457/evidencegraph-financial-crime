import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta

import pytest

from evidencegraph.api.auth import InvalidTokenError, verify_hs256_token


def _segment(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(encoded).rstrip(b"=").decode()


def _token(payload: dict[str, object], *, secret: str = "test-secret") -> str:
    header = _segment({"alg": "HS256", "typ": "JWT"})
    body = _segment(payload)
    signature = hmac.new(secret.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
    return f"{header}.{body}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}"


def test_signed_jwt_requires_signature_issuer_audience_expiry_and_subject() -> None:
    now = datetime(2026, 9, 15, tzinfo=UTC)
    token = _token(
        {
            "sub": "analyst_1",
            "iss": "evidencegraph",
            "aud": "evidencegraph-api",
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        }
    )
    assert (
        verify_hs256_token(
            token,
            secret="test-secret",
            issuer="evidencegraph",
            audience="evidencegraph-api",
            now=now,
        )
        == "analyst_1"
    )

    with pytest.raises(InvalidTokenError, match="signature"):
        verify_hs256_token(
            token,
            secret="wrong-secret",
            issuer="evidencegraph",
            audience="evidencegraph-api",
            now=now,
        )


def test_signed_jwt_rejects_expired_token() -> None:
    now = datetime(2026, 9, 15, tzinfo=UTC)
    token = _token(
        {
            "sub": "analyst_1",
            "iss": "evidencegraph",
            "aud": "evidencegraph-api",
            "exp": int((now - timedelta(seconds=1)).timestamp()),
        }
    )
    with pytest.raises(InvalidTokenError, match="expired"):
        verify_hs256_token(
            token,
            secret="test-secret",
            issuer="evidencegraph",
            audience="evidencegraph-api",
            now=now,
        )
