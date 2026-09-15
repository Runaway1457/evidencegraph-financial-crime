import hashlib
import json
from collections.abc import Mapping
from typing import Any


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def canonical_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256_bytes(encoded)
