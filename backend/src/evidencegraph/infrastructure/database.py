from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from evidencegraph.config import Settings


def build_engine(settings: Settings) -> Engine:
    if settings.database_url.startswith("sqlite"):
        return create_engine(
            settings.database_url,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False},
        )
    return create_engine(settings.database_url, pool_pre_ping=True)


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    session = factory()
    try:
        with session.begin():
            yield session
    finally:
        session.close()
