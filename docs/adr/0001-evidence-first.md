# ADR 0001: Evidence-first findings

- Status: Accepted
- Date: 2026-09-14

## Context

Generative models can produce fluent but unsupported statements. In financial-crime investigations, an unsupported claim can create legal, operational, and reputational harm.

## Decision

The platform models immutable evidence separately from derived entities, relationships, hypotheses, and findings. Relationships and findings must cite evidence identifiers belonging to the same case. AI agents may propose hypotheses only through structured output. The application validates every citation before persistence, and an independent reviewer resolves the proposal.

## Consequences

- Explanations remain traceable to source material.
- Model replacement does not rewrite historical evidence.
- Database constraints and application invariants duplicate critical guarantees intentionally.
- Ingestion and review workflows are more explicit and operationally expensive.
- Evaluation can measure citation validity independently from narrative quality.
