# syntax=docker/dockerfile:1

FROM node:24-alpine AS assets

WORKDIR /build

COPY package.json package-lock.json ./
RUN npm ci

COPY app/styles ./app/styles
COPY app/templates ./app/templates
COPY app/static/js ./app/static/js
RUN npm run build


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

ARG PIPENV_VERSION=2026.6.2
RUN pip install --no-cache-dir "pipenv==${PIPENV_VERSION}"

COPY Pipfile Pipfile.lock ./
RUN pipenv sync --system

COPY app ./app
COPY --from=assets /build/app/static/css/app.css ./app/static/css/app.css

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/temp \
    && chown appuser:appuser /app/temp

USER appuser

EXPOSE 5050

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5050/healthz', timeout=3)"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5050", "--workers", "2"]
