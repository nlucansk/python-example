# --- Build stage ---
FROM ghcr.io/astral-sh/uv:0.6-python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /build
COPY pyproject.toml ./
# Generate lockfile, then install deps (without project itself for caching)
RUN uv lock && uv sync --no-dev --no-install-project

COPY src/ src/
RUN uv sync --no-dev

# --- Runtime stage ---
FROM python:3.12-slim-bookworm

RUN groupadd -r app && useradd -r -g app -d /app -s /sbin/nologin app

COPY --from=builder /build/.venv /app/.venv
COPY --from=builder /build/src /app/src
ENV PATH="/app/.venv/bin:$PATH" \
    VIRTUAL_ENV="/app/.venv" \
    PYTHONPATH="/app/src"

WORKDIR /app
USER app

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
