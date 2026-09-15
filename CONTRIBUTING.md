# Contributing

## Development workflow

1. Create a focused branch from `main`.
2. Add or update tests with every behavior change.
3. Run `make quality` and the frontend quality commands.
4. Explain architectural decisions in an ADR when they affect trust boundaries or long-term coupling.
5. Open a pull request using the repository template.
6. Merge only after required checks pass.

## Commit style

Use Conventional Commits with a focused scope, for example:

```text
feat(ledger): verify evidence bytes on read
fix(workflow): make finding persistence idempotent
docs(adr): record graph projection boundary
```

## Definition of done

A change is not complete because a happy-path demo works. It must include relevant failure behavior, authorization, auditability, observability, tests, migration/deployment impact, and documentation.

## Authorial standard

Repository communication must sound like engineering work owned by its author, not generated collateral.

- Do not describe the system as a “portfolio project” or claim seniority in prose.
- Do not use generic superlatives, invented adoption metrics, decorative architecture, or badge walls.
- State implemented behavior, measured quality and known limitations precisely.
- Keep README claims synchronized with executable tests, migrations and runtime paths.
- Record consequential trade-offs in ADRs so technical judgment remains reviewable.
- Prefer a small number of information-dense diagrams and real product captures.
- Remove template residue, placeholder identities and dead configuration before review.

## AI-assisted contributions

AI assistance is permitted as an engineering tool. It is never accepted as authorship, evidence or review. The contributor remains accountable for every line and decision; suggested output must be understood, edited into the repository's own voice, tested, licensed appropriately and kept free of sensitive information.

See [Engineering standard](docs/engineering-standard.md) for the repository-wide evidence and communication contract.
