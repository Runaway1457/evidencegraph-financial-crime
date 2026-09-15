class DomainError(ValueError):
    """Base error for a violated domain invariant."""


class NotFoundError(DomainError):
    """Requested aggregate does not exist."""


class EvidenceIntegrityError(DomainError):
    """Evidence bytes or provenance do not match the ledger."""


class AuthorizationDeniedError(DomainError):
    """Policy denied an attempted action."""


class ConcurrencyError(DomainError):
    """Aggregate changed after it was read and must be retried."""
