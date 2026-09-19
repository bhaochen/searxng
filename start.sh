#!/usr/bin/env bash
# 一键启动 searxng (Arch Linux + Docker Compose v2)
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

PORT="${SEARXNG_PORT:-8080}"
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  set -a; source ./.env; set +a
  PORT="${SEARXNG_PORT:-8080}"
fi

command -v docker >/dev/null || { echo "缺 docker,先装: sudo pacman -S docker docker-compose"; exit 1; }
docker compose version >/dev/null || { echo "缺 docker compose 插件"; exit 1; }

if ! systemctl is-active --quiet docker; then
  echo "docker.service 未运行,正在启动..."
  sudo systemctl start docker.service
fi

docker compose up -d
docker compose ps
echo "已启动: http://localhost:${PORT}"
