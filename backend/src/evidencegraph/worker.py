import signal
import time

from evidencegraph.application.services import InvestigationService
from evidencegraph.config import get_settings
from evidencegraph.infrastructure.database import build_engine, build_session_factory
from evidencegraph.infrastructure.deterministic_agent import DeterministicInvestigator
from evidencegraph.infrastructure.dispatcher import OutboxDispatcher
from evidencegraph.infrastructure.policy import DevelopmentPolicy, OpaPolicyClient
from evidencegraph.infrastructure.sqlalchemy_repository import SqlAlchemyCaseRepository


def main() -> None:
    settings = get_settings()
    engine = build_engine(settings)
    factory = build_session_factory(engine)
    repository = SqlAlchemyCaseRepository(factory)
    policy = OpaPolicyClient(base_url=settings.opa_url) if settings.opa_url else DevelopmentPolicy()
    dispatcher = OutboxDispatcher(
        factory,
        InvestigationService(repository, DeterministicInvestigator(), policy),
        lease_seconds=settings.outbox_lease_seconds,
        max_attempts=settings.outbox_max_attempts,
    )
    stopping = False

    def stop(_: int, __: object) -> None:
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        while not stopping:
            if dispatcher.dispatch_batch() == 0:
                time.sleep(settings.outbox_poll_seconds)
    finally:
        if isinstance(policy, OpaPolicyClient):
            policy.close()
        engine.dispose()


if __name__ == "__main__":
    main()
