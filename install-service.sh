#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UNIT_DIR="${HOME}/.config/systemd/user"
UNIT_FILE="${UNIT_DIR}/searxng-wake.service"

mkdir -p "${UNIT_DIR}"
python3 - "${ROOT}" "${ROOT}/searxng-wake.service.in" "${UNIT_FILE}" <<'PY'
import pathlib
import sys

root, source, target = sys.argv[1:4]
text = pathlib.Path(source).read_text(encoding="utf-8")
text = text.replace("@SEARXNG_HOME@", root)
pathlib.Path(target).write_text(text, encoding="utf-8")
PY

systemctl --user daemon-reload
systemctl --user enable --now searxng-wake.service
systemctl --user status searxng-wake.service --no-pager || true
