# Release checklist

A release is publishable only when every applicable gate below is evidenced in CI or explicitly waived in the pull request with an owner and expiry.

## Product

- [ ] Primary workflow is understandable without repository context
- [ ] Synthetic demo opens at the documented URL
- [ ] Empty, loading, denied and degraded states are intentional
- [ ] Keyboard and responsive behavior verified
- [ ] Screenshot regenerated from the release bundle

## Backend and data

- [ ] Unit, integration and API tests pass
- [ ] Branch-aware coverage remains above the configured gate
- [ ] Alembic upgrade succeeds on a blank database
- [ ] `alembic check` reports no drift
- [ ] Same-case foreign-key invariants verified
- [ ] Audit and custody hash-chain tests pass
- [ ] Retry and idempotency tests pass

## AI and policy

- [ ] Versioned grounding eval dataset passes
- [ ] False-accept count is zero
- [ ] Policy tests pass with the production policy engine
- [ ] Agent batch rollback and citation validation pass
- [ ] Four-eyes review remains enforced
- [ ] Model and data cards reflect the release

## Supply chain and deployment

- [ ] Dependency installation uses committed lockfiles
- [ ] Runtime dependency audit has no high-severity finding
- [ ] Containers build from clean context
- [ ] Containers run non-root with read-only filesystems
- [ ] Full Compose stack smoke passes
- [ ] Health and readiness endpoints pass
- [ ] No secret or regulated record exists in source, image or artifact

## Publication

- [ ] README claims match verified evidence
- [ ] Changelog and version agree
- [ ] Architecture and runbook match current behavior
- [ ] PR contains verification evidence and rollback notes
- [ ] LinkedIn assets use the current screenshot and repository URL
