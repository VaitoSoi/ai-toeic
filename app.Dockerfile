FROM python:3.14-bookworm

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

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5173"]