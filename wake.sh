#!/usr/bin/env bash
set -euo pipefail
PORT="${SEARXNG_PROXY_PORT:-8080}"
curl --fail --silent --show-error "http://127.0.0.1:${PORT}/wake"
printf '\n'
