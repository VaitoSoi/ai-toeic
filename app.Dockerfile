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

# Default things
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./

# Lint
RUN uv export --frozen --no-dev -o requirements.txt

FROM python:3.14-bookworm

# Default things
WORKDIR /app
VOLUME /app/data
EXPOSE 5173
ENV PATH="/app/.venv/bin:$PATH"
ENV ENV="PROD"

# Copy installed backend library
COPY --from=backend-exporter /app/ /app/

# Install deps
RUN pip install -r requirements.txt

# Lint
RUN ruff check .

# Copy built frontend assets to a directory FastAPI can serve
COPY --from=frontend-builder /app/frontend/dist /app/static

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5173"]