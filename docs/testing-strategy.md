# Testing strategy

Tests are selected by failure cost and trust boundary, not by file count.

## Executed suites

| Suite | Current responsibility |
|---|---|
| Domain | canonical digests, same-case ownership, four-eyes review, terminal review state, graph paths and hash chains |
| Application | batch grounding, rollback, policy denial, requester/generator identity and retry idempotency |
| Persistence | composite foreign keys, unique finding signatures, optimistic locking, audit/custody persistence and append-only guards |
| Reliability | outbox lease, retry, dead-letter behavior and end-to-end worker completion |
| API | bounded binary ingestion, redacted errors, paginated cases, asynchronous runs and review flow |
| Identity | token signature, issuer, audience, expiry and subject checks |
| Frontend | graph inspection, keyboard flow, governance state, explicit demo mode and live case-summary binding |
| Policy | Rego allow/deny behavior and review obligations |
| AI evaluation | citation existence, case scope, duplicate citations and confidence bounds against a versioned synthetic corpus |
| Stack smoke | clean PostgreSQL migration, seed, OPA, API, worker, Nginx, queued run, completed finding and independent review |

## Release gates

- Ruff lint and formatting
- strict MyPy
- backend branch-aware coverage ≥ 80%
- ESLint and TypeScript build
- frontend lines/statements ≥ 70%, functions ≥ 65%, branches ≥ 60%
- Alembic clean-database upgrade and drift check
- OPA policy tests
- lock-enforced Python and npm installs, plus blocking Python and frontend dependency audits
- Docker Compose validation and HTTP stack smoke in GitHub Actions

The local environment used for development does not include Docker. Container and PostgreSQL integration are therefore release claims only after the connected GitHub Actions job passes; local SQLite results are not substituted for that evidence.

## Next quality gates

- mutation testing for the highest-risk domain invariants;
- OIDC/JWKS contract tests when that adapter exists;
- S3, malware scanner, OCR and PII adapter contracts;
- performance budgets for large graph and evidence projections;
- chaos tests around worker termination and lease recovery.

Coverage is a floor. A branch count never replaces assertions about unsafe failure behavior.
