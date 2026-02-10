FROM --platform=$BUILDPLATFORM ghcr.io/astral-sh/uv:python3.14-trixie AS installer

# Default things
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"

# Install dependencies
COPY backend/pyproject.toml backend/uv.lock* ./
RUN uv sync --frozen

COPY backend/ .

# Lint
RUN uv run ruff check .

FROM python:3.14-bookworm

# Default things
WORKDIR /app
VOLUME /app/data
EXPOSE 5173
ENV ENV="PROD"

COPY --from=installer /app/ /app/
ENV PATH="/app/.venv/bin:$PATH"

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5173"]