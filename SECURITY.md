# Security policy

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub private vulnerability reporting for this repository. Include the affected revision, impact, reproduction steps, and any suggested mitigation.

## Supported versions

Only the latest tagged release receives security fixes while this project is pre-1.0.

## Data policy

The repository and demonstration environment must contain synthetic data only. Never commit customer records, credentials, tokens, private keys, production traces, or model inputs derived from real investigations.

## Engineering policy

- Secrets belong in an external secret manager.
- Production authentication must use OIDC; development identity headers are disabled in production.
- Policy and identity dependencies fail closed.
- AI output is untrusted until structurally validated and grounded.
- Findings require independent human review.
- Security exceptions require an owner, rationale, compensating controls, and expiry date.
