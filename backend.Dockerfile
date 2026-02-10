# Stage 1: Install dependencies + lint
FROM --platform=$BUILDPLATFORM ghcr.io/astral-sh/uv:python3.14-bookworm AS builder

ARG TARGETPLATFORM

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock ./
COPY backend/ ./src/

RUN uv run ruff check ./src/

RUN case "$TARGETPLATFORM" in \
      "linux/amd64")  PLAT="x86_64-unknown-linux-gnu" ;; \
      "linux/arm64")  PLAT="aarch64-unknown-linux-gnu" ;; \
      *)              PLAT="" ;; \
    esac && \
    uv sync --frozen --no-dev \
      --python-platform "$PLAT"


# Stage 2: Run code
FROM python:3.14-bookworm

WORKDIR /app
VOLUME /app/data
EXPOSE 5173
ENV ENV="PROD"
ENV PATH="/app/.venv/bin:$PATH"

# Copy pre-downloaded .venv
COPY --from=builder /app/.venv /app/.venv

# Copy backend source code
COPY backend/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5173"]