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

## AI-assisted contributions

AI assistance is permitted, but the contributor remains accountable for every line. Generated output must be reviewed, tested, licensed appropriately, and free of sensitive information.
