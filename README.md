# EvidenceGraph Financial Crime

Evidence-first financial-crime investigation platform combining knowledge graphs, deterministic detection, governed AI agents, document intelligence, durable workflows, and human review.

> Status: active production-grade reconstruction. The default branch is intentionally minimal while the validated implementation is built on a review branch.

## Product principle

The language model is not the source of truth.

```text
Evidence → Entity/Relationship → Graph Path → Hypothesis → Policy Check → Human Review → Finding
```

Every material claim must resolve to immutable evidence and provenance. AI may propose hypotheses; it cannot silently promote them to verified facts.

## Target architecture

- FastAPI application with a strict domain/application/infrastructure boundary
- PostgreSQL system of record and Alembic migrations
- Evidence ledger, SHA-256 integrity, and chain of custody
- Knowledge-graph port with multi-hop traversal and OpenSPG/KAG adapter boundary
- Deterministic financial-crime detectors plus governed agentic reasoning
- OPA policy enforcement and independent four-eyes review
- Temporal workflows backed by a transactional outbox
- S3-compatible object storage, OCR, PII controls, and malware scanning
- React + TypeScript investigation workspace with Cytoscape graph exploration
- OpenTelemetry/Langfuse-compatible observability and reproducible AI evaluations
- Docker Compose for demonstration and Kubernetes/Helm for deployment

## Portfolio-quality documentation

The final README is a release deliverable, not a placeholder. It will include verified screenshots, an investigation walkthrough, system and trust-boundary diagrams, reproducible benchmarks/evals, test evidence, security posture, deployment modes, and engineering trade-offs.

## Security posture

This repository uses synthetic data only. It is designed to demonstrate architecture and engineering controls; it is not a certified AML decision system and must not be deployed against real financial data without institution-specific validation, legal review, model-risk governance, and operational hardening.
