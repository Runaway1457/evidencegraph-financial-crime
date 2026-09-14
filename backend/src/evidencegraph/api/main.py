from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Engine, text

from evidencegraph import __version__
from evidencegraph.api.schemas import CaseResponse, CreateCaseRequest, HealthResponse
from evidencegraph.application.ports import CaseRepository
from evidencegraph.application.services import CaseService
from evidencegraph.config import Settings, get_settings
from evidencegraph.domain.errors import DomainError, NotFoundError
from evidencegraph.infrastructure.database import build_engine, build_session_factory
from evidencegraph.infrastructure.sqlalchemy_repository import SqlAlchemyCaseRepository


def create_app(
    *,
    settings_override: Settings | None = None,
    repository_override: CaseRepository | None = None,
) -> FastAPI:
    settings = settings_override or get_settings()
    engine: Engine | None = None

    if repository_override is None:
        engine = build_engine(settings)
        repository: CaseRepository = SqlAlchemyCaseRepository(build_session_factory(engine))
    else:
        repository = repository_override

    service = CaseService(repository)
    application = FastAPI(
        title="EvidenceGraph Financial Crime",
        version=__version__,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url=None,
    )
    application.state.case_service = service
    application.state.engine = engine
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-Actor-ID"],
    )

    def actor_id(x_actor_id: Annotated[str | None, Header()] = None) -> str:
        if settings.auth_mode == "development":
            return x_actor_id or "development-investigator"
        if not x_actor_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return x_actor_id

    @application.get("/health/live", response_model=HealthResponse, tags=["health"])
    def live() -> HealthResponse:
        return HealthResponse(status="ok", version=__version__)

    @application.get("/health/ready", response_model=HealthResponse, tags=["health"])
    def ready() -> HealthResponse:
        if engine is not None:
            try:
                with engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="database unavailable",
                ) from exc
        return HealthResponse(status="ready", version=__version__)

    @application.get(
        f"{settings.api_prefix}/cases",
        response_model=list[CaseResponse],
        tags=["cases"],
    )
    def list_cases() -> list[CaseResponse]:
        return [CaseResponse.from_domain(case) for case in service.list_cases()]

    @application.post(
        f"{settings.api_prefix}/cases",
        response_model=CaseResponse,
        status_code=status.HTTP_201_CREATED,
        tags=["cases"],
    )
    def create_case(
        payload: CreateCaseRequest,
        actor: Annotated[str, Depends(actor_id)],
    ) -> CaseResponse:
        try:
            case = service.create_case(
                title=payload.title,
                description=payload.description,
                actor_id=actor,
            )
        except DomainError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc
        return CaseResponse.from_domain(case)

    @application.get(
        f"{settings.api_prefix}/cases/{{case_id}}",
        response_model=CaseResponse,
        tags=["cases"],
    )
    def get_case(case_id: str) -> CaseResponse:
        try:
            return CaseResponse.from_domain(service.get_case(case_id))
        except NotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="case not found",
            ) from exc

    return application


app = create_app()
