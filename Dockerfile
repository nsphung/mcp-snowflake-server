# syntax=docker/dockerfile:1

# This image is using Docker Hardened Images (DHI) as a base, which provides a secure foundation for building containerized applications. The Dockerfile is structured in multiple stages to optimize the build process and ensure a minimal runtime image.
# Source: https://docs.docker.com/dhi/
# You must have access to the DHI registry to build this image. If you don't have access, you can replace the base images with standard Debian-based Python images, but be aware that you may lose some of the security benefits provided by DHI.
# See https://docs.docker.com/dhi/get-started/ to have an account and get access to the DHI registry.
# docker login dhi.io

# --- Stage 0: uv binary ---
FROM dhi.io/uv:0-debian13-dev AS uv

# --- Stage 1: Build ---
FROM dhi.io/python:3.13-debian13-dev AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY --from=uv /usr/local/bin/uv /usr/local/bin/uvx /bin/

WORKDIR /app

# Install system deps needed by snowflake-connector-python
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Dependency layer (cached unless pyproject.toml/uv.lock change)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Application layer
COPY README.md runtime_config.json LICENSE ./
COPY src/ src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# --- Stage 2: Runtime (hardened, no shell, nonroot) ---
FROM dhi.io/python:3.13-debian13

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

COPY --from=builder --chown=nonroot:nonroot /app/.venv /app/.venv
COPY --chown=nonroot:nonroot runtime_config.json ./

USER nonroot

ENTRYPOINT ["mcp_snowflake_server"]
