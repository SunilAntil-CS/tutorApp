# syntax=docker/dockerfile:1
# Production-grade Dockerfile for FastAPI backend

# ---- Builder ----
FROM python:3.11-slim-bookworm as builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---- Runtime ----
FROM python:3.11-slim-bookworm as runtime

RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --shell /bin/bash --create-home app

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.local/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/* && rm -rf /wheels

COPY --chown=app:app . .

# So the app user can write logs when LOG_FILE is used (e.g. logs/backend.log).
RUN mkdir -p /app/logs && chown -R app:app /app/logs

USER app

EXPOSE 8000

HEALTHCHECK --interval=60s --timeout=5s --start-period=15s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

# 7. Production Command: Added proxy headers for Coolify's Traefik proxy
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips='*'"]