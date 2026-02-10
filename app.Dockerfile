# Stage 1: Frontend
FROM --platform=$BUILDPLATFORM node:24-alpine AS frontend-builder

WORKDIR /app/frontend

# For yarn
RUN corepack enable

# Yarn & package things
COPY frontend/package.json frontend/yarn.lock frontend/.yarnrc.yml* ./
COPY frontend/.yarn ./.yarn

# Install dependencies
RUN yarn install --immutable

COPY frontend/ .

# Lint & build
ENV VITE_BACKEND_URL="/api"
RUN yarn lint
RUN yarn build

# Stage 2: Backend Exporter - Export uv to requirements.txt file
FROM --platform=$BUILDPLATFORM ghcr.io/astral-sh/uv:debian-slim AS backend-exporter

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

# Copy built frontend assets to a directory FastAPI can serve
COPY --from=frontend-builder /app/frontend/dist /app/static

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5173"]