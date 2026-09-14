#!/usr/bin/env bash
set -euo pipefail

APP_DIR=/srv/RNA_Grainy_App
BRANCH=main
cd "$APP_DIR"

echo "==> Fetching origin/$BRANCH"
git fetch --prune --tags origin

PREV=$(git rev-parse --short HEAD)
git reset --hard "origin/$BRANCH"

echo "==> $PREV -> $(git rev-parse --short HEAD)"

echo "==> Determining application version"

GIT_VERSION=$(
  git describe --tags --exact-match HEAD 2>/dev/null \
    || printf 'dev-%s' "$(git rev-parse --short HEAD)"
)

export APP_VERSION="${GIT_VERSION#v}"

echo "==> Deploying RNAgrainy ${APP_VERSION}"

echo "==> Building and starting containers"
docker compose up -d --build
docker compose ps

echo "==> Health check"
for i in $(seq 1 30); do
  if curl -fsS -o /dev/null http://127.0.0.1:5050/healthz; then
    echo "healthy after ${i}s"
    docker image prune -f
    exit 0
  fi
  sleep 1
done

echo "!! health check FAILED !!"
docker compose logs --tail 40
exit 1
