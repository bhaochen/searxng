#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

if [[ "${1:-}" == "--backend" ]]; then
  if [[ -f .env ]]; then
    # shellcheck disable=SC1091
    set -a; source ./.env; set +a
  fi
  command -v docker >/dev/null || { echo "缺 docker,先装: sudo pacman -S docker docker-compose"; exit 1; }
  docker compose version >/dev/null || { echo "缺 docker compose 插件"; exit 1; }
  if ! systemctl is-active --quiet docker; then
    echo "docker.service 未运行,正在启动..."
    sudo systemctl start docker.service
  fi
  docker compose up -d --wait
  docker compose ps
  echo "已启动后端: http://127.0.0.1:${SEARXNG_BACKEND_PORT:-18080}"
  exit 0
fi

./install-service.sh
  PORT="${SEARXNG_PROXY_PORT:-18081}"

if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  set -a; source ./.env; set +a
PORT="${SEARXNG_PROXY_PORT:-18081}"

fi
echo "已启动按需代理: http://127.0.0.1:${PORT}"
echo "首次请求会拉起 SearXNG，空闲 ${SEARXNG_IDLE_TIMEOUT_SECONDS:-300}s 后自动休眠。"
