FROM python:3.14.7-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.11 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/evidencegraph

WORKDIR /build
COPY pyproject.toml uv.lock README.md ./
COPY backend ./backend
RUN uv sync --locked --no-dev --no-editable

FROM python:3.14.7-slim-bookworm AS runtime

ENV VIRTUAL_ENV=/opt/evidencegraph \
    PATH="/opt/evidencegraph/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN groupadd --gid 10001 evidencegraph \
    && useradd --uid 10001 --gid evidencegraph --no-create-home evidencegraph

WORKDIR /app
COPY --from=builder /opt/evidencegraph /opt/evidencegraph
COPY alembic.ini ./
COPY backend/migrations ./backend/migrations
COPY scripts ./scripts

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=20s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)"

CMD ["uvicorn", "evidencegraph.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
