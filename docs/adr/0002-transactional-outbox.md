# ADR 0002: Transactional outbox for workflow dispatch

- Status: Accepted
- Date: 2026-09-14

## Context

Creating an investigation run in PostgreSQL and starting a Temporal workflow are two writes to different systems. A process crash between them can create a committed run that never starts, or a retry can start the workflow more than once.

## Decision

The API writes `investigation_runs`, `workflow_outbox`, and the audit event in one database transaction. A separate dispatcher leases pending messages with `FOR UPDATE SKIP LOCKED`, uses the run ID as Temporal's deterministic workflow ID, and marks the message dispatched only after Temporal accepts it.

Dispatch is at-least-once. Workflow start and every state-changing activity must therefore be idempotent. Messages use exponential retry and move to a dead-letter state after the configured attempt limit.

## Consequences

- Database commit no longer depends on Temporal availability.
- Recovery is observable and replayable.
- Dispatcher concurrency is safe across replicas.
- Operations must monitor backlog age, retry rate, and dead letters.
- Exactly-once delivery is not claimed; effects are made idempotent.
