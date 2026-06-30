#!/usr/bin/env bash
# Fixed local entry point for the Codex backend. Keeps Codex logs/results
# separate from Claude Code under log/<run_group>/codex/.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
mkdir -p "$ROOT/log" "$HERE/codex/cli_home"

set -a; [ -f "$ROOT/.env" ] && source "$ROOT/.env"; set +a
unset ALL_PROXY HTTPS_PROXY HTTP_PROXY all_proxy https_proxy http_proxy NO_PROXY no_proxy || true

if [ -z "${FUTURECAST_RUN_DATE:-}" ]; then
  export FUTURECAST_RUN_DATE="$(date +%F)"
fi
if [ -z "${FUTURECAST_RUN_GROUP:-}" ]; then
  export FUTURECAST_RUN_GROUP="$(date +%Y%m%d-%H%M%S)"
fi
if [ -n "${GPT_sub2api_apikey:-}" ] && [ -z "${SUB2API_API_KEY:-}" ]; then
  export SUB2API_API_KEY="$GPT_sub2api_apikey"
fi
if [ -z "${SUB2API_BASE_URL:-}" ]; then
  export SUB2API_BASE_URL="https://ie-crs.haoxiang.ai/v1"
fi

"$ROOT/.venv/bin/python" "$HERE/codex/run_forecast.py" "$@"
