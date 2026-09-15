from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Engine, text

from evidencegraph import __version__
from evidencegraph.api.auth import InvalidTokenError, verify_hs256_token
from evidencegraph.api.schemas import (
    CaseResponse,
    CreateCaseRequest,
    EvidenceResponse,
    FindingResponse,
    HealthResponse,
    InvestigationRunResponse,
    ReviewFindingRequest,
)
from evidencegraph.application.ports import CaseRepository, InvestigationQueue, ObjectStore
from evidencegraph.application.services import CaseService, InvestigationService
from evidencegraph.config import Settings, get_settings
from evidencegraph.domain.errors import AuthorizationDeniedError, DomainError, NotFoundError
from evidencegraph.domain.models import EvidenceType, new_id
from evidencegraph.infrastructure.database import build_engine, build_session_factory
from evidencegraph.infrastructure.deterministic_agent import DeterministicInvestigator
from evidencegraph.infrastructure.object_store import FileSystemObjectStore
from evidencegraph.infrastructure.policy import DevelopmentPolicy, OpaPolicyClient
from evidencegraph.infrastructure.run_queue import (
    InMemoryInvestigationQueue,
    SqlAlchemyInvestigationQueue,
)
from evidencegraph.infrastructure.sqlalchemy_repository import SqlAlchemyCaseRepository
from evidencegraph.observability import configure_logging, install_http_observability


def create_app(
    *,
    settings_override: Settings | None = None,
    repository_override: CaseRepository | None = None,
    object_store_override: ObjectStore | None = None,
    queue_override: InvestigationQueue | None = None,
) -> FastAPI:
    settings = settings_override or get_settings()
    configure_logging(settings.log_level)
    engine: Engine | None = None

    if repository_override is None:
        engine = build_engine(settings)
        session_factory = build_session_factory(engine)
        repository: CaseRepository = SqlAlchemyCaseRepository(session_factory)
        queue: InvestigationQueue = queue_override or SqlAlchemyInvestigationQueue(session_factory)
    else:
        repository = repository_override
        queue = queue_override or InMemoryInvestigationQueue()

    object_store = object_store_override or FileSystemObjectStore(settings.object_store_path)
    service = CaseService(repository, object_store)
    policy = OpaPolicyClient(base_url=settings.opa_url) if settings.opa_url else DevelopmentPolicy()
    investigation_service = InvestigationService(repository, DeterministicInvestigator(), policy)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            if isinstance(policy, OpaPolicyClient):
                policy.close()
            if engine is not None:
                engine.dispose()

    application = FastAPI(
        title="EvidenceGraph Financial Crime",
        version=__version__,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url=None,
        lifespan=lifespan,
    )
    application.state.case_service = service
    application.state.investigation_service = investigation_service
    application.state.investigation_queue = queue
    application.state.engine = engine
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-Actor-ID", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
    install_http_observability(application)

    def actor_id(
        authorization: Annotated[str | None, Header()] = None,
        x_actor_id: Annotated[str | None, Header()] = None,
    ) -> str:
        if settings.auth_mode == "development":
            return x_actor_id or "development-investigator"
        if authorization is None or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="bearer token required",
            )
        assert settings.jwt_secret is not None
        try:
            return verify_hs256_token(
                authorization.removeprefix("Bearer ").strip(),
                secret=settings.jwt_secret.get_secret_value(),
                issuer=settings.jwt_issuer,
                audience=settings.jwt_audience,
            )
        except InvalidTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid bearer token",
            ) from exc

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
    def list_cases(
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
        offset: Annotated[int, Query(ge=0)] = 0,
    ) -> list[CaseResponse]:
        return [
            CaseResponse.from_domain(case)
            for case in service.list_cases(limit=limit, offset=offset)
        ]

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
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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

    @application.post(
        f"{settings.api_prefix}/cases/{{case_id}}/evidence",
        response_model=EvidenceResponse,
        status_code=status.HTTP_201_CREATED,
        tags=["evidence"],
    )
    async def ingest_evidence(
        case_id: str,
        request: Request,
        actor: Annotated[str, Depends(actor_id)],
        evidence_type: Annotated[EvidenceType, Query()],
        source: Annotated[str, Query(min_length=1, max_length=512)],
    ) -> EvidenceResponse:
        declared_length = request.headers.get("content-length")
        if declared_length is not None:
            try:
                if int(declared_length) > settings.max_upload_bytes:
                    raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="invalid content-length",
                ) from exc

        content = bytearray()
        async for chunk in request.stream():
            content.extend(chunk)
            if len(content) > settings.max_upload_bytes:
                raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="evidence payload cannot be empty",
            )

        try:
            evidence = service.ingest_evidence(
                case_id=case_id,
                content=bytes(content),
                evidence_type=evidence_type,
                source=source,
                storage_key=f"{case_id}/{new_id('object')}",
                actor_id=actor,
                media_type=request.headers.get("content-type", "application/octet-stream"),
            )
        except NotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="case not found",
            ) from exc
        except DomainError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc
        return EvidenceResponse.model_validate(evidence)

    @application.get(
        f"{settings.api_prefix}/cases/{{case_id}}/findings",
        response_model=list[FindingResponse],
        tags=["investigations"],
    )
    def list_findings(case_id: str) -> list[FindingResponse]:
        try:
            case = service.get_case(case_id)
        except NotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="case not found",
            ) from exc
        return [FindingResponse.from_domain(item) for item in case.findings]

    @application.post(
        f"{settings.api_prefix}/cases/{{case_id}}/investigations",
        response_model=InvestigationRunResponse,
        status_code=status.HTTP_202_ACCEPTED,
        tags=["investigations"],
    )
    def run_investigation(
        case_id: str,
        actor: Annotated[str, Depends(actor_id)],
    ) -> InvestigationRunResponse:
        try:
            investigation_service.authorize_run(case_id=case_id, actor_id=actor)
            run = queue.enqueue(case_id=case_id, actor_id=actor)
        except AuthorizationDeniedError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="policy denied",
            ) from exc
        except NotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="case not found",
            ) from exc
        return InvestigationRunResponse.from_domain(run)

    @application.get(
        f"{settings.api_prefix}/investigation-runs/{{run_id}}",
        response_model=InvestigationRunResponse,
        tags=["investigations"],
    )
    def get_investigation_run(run_id: str) -> InvestigationRunResponse:
        run = queue.get(run_id)
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="investigation run not found",
            )
        return InvestigationRunResponse.from_domain(run)

    @application.post(
        f"{settings.api_prefix}/cases/{{case_id}}/findings/{{finding_id}}/review",
        response_model=FindingResponse,
        tags=["investigations"],
    )
    def review_finding(
        case_id: str,
        finding_id: str,
        payload: ReviewFindingRequest,
        actor: Annotated[str, Depends(actor_id)],
    ) -> FindingResponse:
        try:
            finding = investigation_service.review(
                case_id=case_id,
                finding_id=finding_id,
                reviewer_id=actor,
                decision=payload.decision,
            )
        except AuthorizationDeniedError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="policy denied",
            ) from exc
        except NotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="finding not found",
            ) from exc
        except DomainError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc
        return FindingResponse.from_domain(finding)

    return application


app = create_app()
