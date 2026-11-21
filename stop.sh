#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

docker compose stop

if [[ "${1:-}" == "--all" || "${1:-}" == "--proxy" ]]; then
  systemctl --user stop searxng-wake.service || true
  echo "已停止按需代理。"
fi

echo "已休眠 SearXNG 后端（数据卷保留）。"
