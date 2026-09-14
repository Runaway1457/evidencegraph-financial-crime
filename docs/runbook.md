# Runbook — local stack and first-response operations

## Start

```bash
export POSTGRES_PASSWORD='replace-this-local-secret'
docker compose -f deployment/compose.yaml up --build
```

The web workbench is available on `http://localhost:8080`. The web container proxies
`/health/ready` to the API. Database schema is applied by a one-shot migration service
before the API starts.

## Stop and preserve data

```bash
docker compose -f deployment/compose.yaml down
```

Use `down --volumes` only when intentionally deleting the local PostgreSQL volume.

## Triage

1. Run `docker compose -f deployment/compose.yaml ps`.
2. Inspect the failed service with `docker compose -f deployment/compose.yaml logs SERVICE`.
3. Verify PostgreSQL health and the migration container exit code.
4. Treat OPA errors as authorization denials; do not bypass policy to restore service.
5. Preserve audit and evidence data before rollback.

## Recovery principles

- Re-run migrations; never create tables in the API process.
- Requeue dead-letter outbox records only after the downstream cause is fixed.
- Do not edit audit hashes or chain-of-custody rows.
- Rotate exposed credentials and invalidate affected sessions before restart.
- Record every production recovery in the incident timeline.

## Verification

```bash
curl --fail http://localhost:8080/health/live
curl --fail http://localhost:8080/health/ready
curl --fail http://localhost:8080/
```
