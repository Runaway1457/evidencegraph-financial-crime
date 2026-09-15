# Testing strategy

Testing is organized by risk, not only by the testing pyramid.

## Suites

1. **Domain unit tests** verify evidence integrity, same-case ownership, four-eyes review, graph grounding, and audit-chain behavior.
2. **Application tests** verify transactions, rollback, idempotency, authorization decisions, and failure translation.
3. **Adapter contracts** run the same behavioral contract against in-memory and production adapters.
4. **Integration tests** use PostgreSQL, S3-compatible storage, OPA, Temporal, and workers.
5. **API tests** cover schemas, limits, identity propagation, error redaction, and concurrency.
6. **Frontend tests** cover evidence visibility, review warnings, graph selection, keyboard behavior, and critical responsive states.
7. **AI evaluations** score citation validity, evidence coverage, unsupported-claim rate, tool-policy compliance, privacy leakage, and resistance to prompt injection.
8. **Release smoke tests** migrate a clean database, seed a synthetic case, execute an investigation, review a finding, export an Evidence Packet, and verify its manifest.

## Gates

- Python lint and format: Ruff
- Python typing: MyPy strict
- Backend branch-aware coverage: minimum 80%
- Frontend lint and strict TypeScript
- Frontend coverage: lines/statements 70%, functions 65%, branches 60%
- Clean build for API and web images
- Migration drift check
- Dependency, secret, CodeQL, SBOM, and container scans
- No critical/high vulnerabilities accepted without an explicit, expiring risk record

Coverage thresholds are floors. Mutation testing and risk-focused assertions are preferred over raising coverage with low-value lines.
