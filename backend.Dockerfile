FROM --platform=$BUILDPLATFORM ghcr.io/astral-sh/uv:python3.14-trixie AS exporter

# Default things
WORKDIR /app
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./

# Lint
RUN uv export --frozen --no-dev -o requirements.txt

FROM python:3.14-bookworm

# Default things
WORKDIR /app
VOLUME /app/data
EXPOSE 5173
ENV ENV="PROD"
ENV PATH="/app/.venv/bin:$PATH"

COPY --from=exporter /app/ /app/

# Install deps
RUN pip install -r requirements.txt

# Lint
RUN ruff check .

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5173"]