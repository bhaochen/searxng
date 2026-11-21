#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
PORT="${SEARXNG_PROXY_PORT:-18081}"
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  set -a; source ./.env; set +a
  PORT="${SEARXNG_PROXY_PORT:-18081}"
fi
curl --fail --silent --show-error "http://127.0.0.1:${PORT}/wake"
printf '\n'
