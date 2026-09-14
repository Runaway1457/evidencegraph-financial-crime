from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from evidencegraph import __version__
from evidencegraph.api.schemas import CaseResponse, CreateCaseRequest, HealthResponse
from evidencegraph.application.services import CaseService
from evidencegraph.config import get_settings
from evidencegraph.domain.errors import DomainError, NotFoundError
from evidencegraph.infrastructure.memory import InMemoryCaseRepository

settings = get_settings()
repository = InMemoryCaseRepository()
service = CaseService(repository)

app = FastAPI(
    title="EvidenceGraph Financial Crime",
    version=__version__,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)
app.add_middleware(
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


@app.get("/health/live", response_model=HealthResponse, tags=["health"])
def live() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)


@app.get(f"{settings.api_prefix}/cases", response_model=list[CaseResponse], tags=["cases"])
def list_cases() -> list[CaseResponse]:
    return [CaseResponse.from_domain(case) for case in service.list_cases()]


@app.post(
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


@app.get(f"{settings.api_prefix}/cases/{{case_id}}", response_model=CaseResponse, tags=["cases"])
def get_case(case_id: str) -> CaseResponse:
    try:
        return CaseResponse.from_domain(service.get_case(case_id))
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case not found") from exc
