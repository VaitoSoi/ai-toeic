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


# Stage 2: Backend
FROM --platform=$BUILDPLATFORM ghcr.io/astral-sh/uv:python3.14-trixie AS backend-installer

# Default things
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"

ARG TARGETPLATFORM="linux"

# Enable bytecode compilation and set the target for cross-platform sync
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Map Docker platform strings to Python platform tags
RUN if [ "$TARGETPLATFORM" = "linux/amd64" ]; then \
        echo "linux" > /tmp/py_platform; \
    elif [ "$TARGETPLATFORM" = "linux/arm64" ]; then \
        echo "aarch64-unknown-linux-gnu" > /tmp/py_platform; \
    else \
        echo "linux" > /tmp/py_platform; \
    fi

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=backend/pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=backend/uv.lock,target=uv.lock \
    # The --python-platform flag ensures we get the right C extensions
    uv sync --frozen --no-install-project --no-dev \
    --python-platform $(cat /tmp/py_platform)
    
COPY backend/ .

# Lint
RUN uv run ruff check .

FROM python:3.14-bookworm

# Default things
WORKDIR /app
VOLUME /app/data
EXPOSE 5173
ENV PATH="/app/.venv/bin:$PATH"
ENV ENV="PROD"

# Copy installed backend library
COPY --from=backend-installer /app/ /app/

# Copy built frontend assets to a directory FastAPI can serve
COPY --from=frontend-builder /app/frontend/dist /app/static

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5173"]