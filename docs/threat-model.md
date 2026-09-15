# Threat model

## Scope

The verified reference path covers synthetic case data, binary evidence ingestion, a PostgreSQL ledger, an atomic local object store, OPA authorization, asynchronous investigation runs, a deterministic investigator and the browser workbench.

OIDC/JWKS, S3, malware scanning, OCR, PII redaction, external model providers and Temporal are extension boundaries and are not treated as deployed controls.

## Protected assets

- Original evidence bytes and canonical digests
- Chain-of-custody and case audit events
- Case-local entities, relationships, hypotheses and review decisions
- Investigator identity and policy context
- Outbox messages, run status and idempotency signatures
- Authentication, database and policy credentials

## High-priority threats

| Threat | Boundary | Enforced controls | Verification |
|---|---|---|---|
| Oversized or malicious upload | client → API | content-length precheck, streamed byte cap, edge body/rate limit, opaque object key | API negative tests |
| Path traversal | API → object store | server-generated key and resolved-root containment | object-store negative test |
| Evidence tampering | storage → ledger | canonical SHA-256, atomic write, custody event, chained case audit | domain and SQL tests |
| Unsupported finding | investigator → application | structured proposal, citation validation, same-case FKs, terminal human review | adversarial evals and service tests |
| Self-approval | analyst → review | human requester persisted separately from generating agent; domain and SQL constraint | domain/API tests |
| Lost concurrent decision | service → PostgreSQL | optimistic case version and compare-and-set update | stale-writer test |
| Duplicate retry effect | worker → finding | canonical signature plus case-local unique constraint | dispatcher and SQL tests |
| Lost workflow request | API → worker | run and outbox committed together, lease, retry and dead letter | outbox/dispatcher tests |
| Forged identity | client → API | signed JWT algorithm, signature, issuer, audience, time and subject validation | identity tests |
| Policy bypass on outage | API → OPA | fail-closed policy client | policy tests |
| Audit rewrite | application/operator → database | ORM mutation guards, PostgreSQL update/delete triggers, chained hashes | persistence test and migration smoke |
| Sensitive error leakage | service → client/log | generic external errors, request IDs and structured route logs | API tests |

## Residual risk

- A database or host administrator remains privileged; external immutable retention and organizational controls are still required.
- HS256 is appropriate for the contained reference profile but not a substitute for institutional OIDC/JWKS key rotation and claims governance.
- The local object store does not provide bucket retention, malware scanning, encryption key separation or regional replication.
- The deterministic baseline finds a narrow two-hop pattern; it is not an AML model, regulatory decision or legal conclusion.
- Graph and evidence detail panels remain synthetic until projection endpoints replace the explicit demo fixture.

Real financial data requires institution-specific AML validation, data residency, retention, incident response, model-risk approval and privacy controls.
