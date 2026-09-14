# Threat model

## Scope

EvidenceGraph processes synthetic financial transactions, corporate records, blockchain events, analyst notes, and uploaded documents. The model covers the application, workers, object storage, database, policy engine, graph projections, model providers, telemetry, and investigator browser.

## Protected assets

- Original evidence bytes and integrity digests
- Chain-of-custody and append-only audit events
- Case membership, relationships, hypotheses, and review decisions
- Investigator identity, role, and authorization context
- Prompt/model inputs, outputs, traces, and evaluation datasets
- Encryption, OIDC, storage, and provider credentials

## High-priority threats and controls

| Threat | Boundary | Primary controls | Verification |
| --- | --- | --- | --- |
| Evidence tampering | upload → storage → ledger | streaming hash, immutable object key, custody event, re-verification | integrity tests |
| Unsupported AI claim | model → application | structured schema, citation validation, same-case constraints, human review | adversarial evals |
| Prompt injection in documents | document → OCR/model | content treated as data, tool allowlist, policy check, separated instructions | injection corpus |
| Cross-case data exposure | API/graph/storage | tenant/case scope in queries, composite constraints, object prefix policy | authorization tests |
| Privilege escalation | browser/API → OIDC/OPA | PKCE, validated issuer/audience, short-lived tokens, OPA fail-closed | contract/security tests |
| Duplicate workflow effects | outbox → Temporal → worker | deterministic workflow IDs, idempotency keys, unique database constraints | retry tests |
| Sensitive traces | application → telemetry | PII redaction before tracing, sensitive trace payloads disabled | telemetry tests |
| Audit deletion/rewrite | database/operator | append-only permissions, hash chain, external retention/export | chain verification |

## Trust assumptions

- Root/cloud/database administrators remain privileged and require organizational controls outside this repository.
- Third-party model and identity providers are independently governed.
- No automated finding is a regulatory filing or legal conclusion.
- Real deployment requires institution-specific AML validation, data residency analysis, retention policy, incident response, and model-risk approval.
