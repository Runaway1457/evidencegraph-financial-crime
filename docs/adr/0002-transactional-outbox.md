# ADR-0002: Commit workflow intent before dispatch

- Status: accepted
- Date: 2026-09-14

## Context

Creating an investigation run and invoking a worker are separate effects. Directly calling a workflow runtime after a PostgreSQL commit leaves a crash window: a durable run may never start, while blind retries may execute the same investigation more than once.

## Decision

The API writes the investigation run, `investigation.requested` outbox message and audit event in one PostgreSQL transaction, then returns `202 Accepted` with the run ID.

A separate worker:

1. leases pending messages with `FOR UPDATE SKIP LOCKED`;
2. marks the run as running;
3. invokes the investigator through the application service;
4. relies on canonical finding signatures and a database unique constraint for idempotency;
5. marks the message dispatched only after the use case completes;
6. applies exponential retry and explicit dead-letter state on failure.

The reference deployment runs this worker directly. Temporal remains an optional future dispatcher adapter; it is not required for the verified path.

## Consequences

- Database commit does not depend on worker availability.
- Queue state and retry history remain inspectable in PostgreSQL.
- At-least-once delivery does not duplicate findings.
- Operators can identify dead-letter runs instead of losing work silently.
- The database carries queue load; a higher-scale deployment may project messages to a dedicated workflow runtime without changing the API contract.
