FROM --platform=$BUILDPLATFORM ghcr.io/astral-sh/uv:python3.14-bookworm AS builder

ARG TARGETPLATFORM

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock ./
COPY backend/ ./src/

# Lint natively
RUN uv run ruff check ./src/

# Download correct wheels for target platform
RUN case "$TARGETPLATFORM" in \
      "linux/amd64")  PLAT="x86_64-unknown-linux-gnu" ;; \
      "linux/arm64")  PLAT="aarch64-unknown-linux-gnu" ;; \
      *)              PLAT="" ;; \
    esac && \
    uv export --frozen --no-dev -o requirements.txt && \
    uv pip install \
      --target /app/deps \
      --python-platform "$PLAT" \
      --only-binary :all: \
      -r requirements.txt


# Final stage — Run code
FROM python:3.14-bookworm

WORKDIR /app
VOLUME /app/data
EXPOSE 5173
ENV ENV="PROD"
ENV PYTHONPATH="/app/deps:$PYTHONPATH"

COPY --from=builder /app/deps /app/deps
COPY backend/ .

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5173"]