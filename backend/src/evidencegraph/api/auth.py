import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime
from typing import Any


class InvalidTokenError(ValueError):
    pass


def _decode_segment(segment: str) -> dict[str, Any]:
    try:
        padded = segment + "=" * (-len(segment) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
    except (ValueError, json.JSONDecodeError) as exc:
        raise InvalidTokenError("token is malformed") from exc
    if not isinstance(payload, dict):
        raise InvalidTokenError("token segment must be an object")
    return payload


def verify_hs256_token(
    token: str,
    *,
    secret: str,
    issuer: str,
    audience: str,
    now: datetime | None = None,
) -> str:
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
    except ValueError as exc:
        raise InvalidTokenError("token is malformed") from exc
    header = _decode_segment(header_segment)
    payload = _decode_segment(payload_segment)
    if header.get("alg") != "HS256" or header.get("typ") not in (None, "JWT"):
        raise InvalidTokenError("token algorithm is not allowed")

    signing_input = f"{header_segment}.{payload_segment}".encode()
    expected = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    try:
        actual = base64.urlsafe_b64decode(signature_segment + "=" * (-len(signature_segment) % 4))
    except ValueError as exc:
        raise InvalidTokenError("token signature is malformed") from exc
    if not hmac.compare_digest(actual, expected):
        raise InvalidTokenError("token signature is invalid")

    clock = int((now or datetime.now(UTC)).timestamp())
    if payload.get("iss") != issuer:
        raise InvalidTokenError("token issuer is invalid")
    token_audience = payload.get("aud")
    audiences = token_audience if isinstance(token_audience, list) else [token_audience]
    if audience not in audiences:
        raise InvalidTokenError("token audience is invalid")
    if not isinstance(payload.get("exp"), int) or payload["exp"] <= clock:
        raise InvalidTokenError("token is expired")
    if isinstance(payload.get("nbf"), int) and payload["nbf"] > clock:
        raise InvalidTokenError("token is not active")
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        raise InvalidTokenError("token subject is missing")
    return subject
