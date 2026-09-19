#!/usr/bin/env bash
# 一键关闭 searxng (保留数据卷,下次 start.sh 照常恢复)
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

command -v docker >/dev/null || { echo "缺 docker"; exit 1; }

docker compose down
echo "已关闭 searxng (数据卷保留)."
echo "如需连数据一起删: docker compose down -v"
docker compose ps
