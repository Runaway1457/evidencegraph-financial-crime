FROM python:3.12.14-slim-bookworm AS builder

ENV VIRTUAL_ENV=/opt/evidencegraph
RUN python -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /build
COPY pyproject.toml README.md ./
COPY backend ./backend
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

FROM python:3.12.14-slim-bookworm AS runtime

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

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=20s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)"

CMD ["uvicorn", "evidencegraph.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
