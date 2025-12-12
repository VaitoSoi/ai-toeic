# Stage 1: Frontend
FROM node:24-alpine AS frontend-builder

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
RUN yarn lint
RUN yarn build


# Stage 2: Backend
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Default things
WORKDIR /app
VOLUME /app/data
EXPOSE 5173
ENV ENV="PROD"
ENV PATH="/app/.venv/bin:$PATH"

# Install dependencies
COPY backend/pyproject.toml backend/uv.lock* ./
RUN uv sync --frozen

COPY backend/ .

# Lint
RUN uv run ruff check .

# Copy built frontend assets to a directory FastAPI can serve
COPY --from=frontend-builder /app/frontend/dist /app/static


# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5173"]