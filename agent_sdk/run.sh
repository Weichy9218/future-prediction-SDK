#!/usr/bin/env bash
# Fixed local entry point — run the forecast agent from THIS repo's own code only.
# No global ccr, no manual `.venv/bin/python ...`. agent_sdk/ is to futurecast what
# pipeline/ is to galaxy-selfevolve: the owned run harness.
#
#   ./agent_sdk/run.sh                          # glm-5, knowledge-only
#   ./agent_sdk/run.sh --tools                  # glm-5, tool-enabled multi-step rollout
#   ./agent_sdk/run.sh --model gpt-5.5 --tools  # gpt-5.5 (haoxiang) through the SAME agent + tools
#
# It (1) regenerates the *local* ccr config from the committed template for the chosen model
# (apihy=glm/qwen, haoxiang=gpt), starts the *vendored* claude-code-router (HOME redirected into
# agent_sdk/ccr_home so nothing in ~ is used), then (2) runs the Agent SDK forecast. The runner
# writes a standardized rollout + result under log/ (see run_forecast.py).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
CCR_HOME="$HERE/ccr_home"
export HOME="$CCR_HOME"                  # ccr + claude CLI both read config/state from here

# Parse args: --model NAME selects the route; --tools enables the tool surface. Both forwarded.
MODEL="glm-5"
PASS_ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --model) MODEL="$2"; PASS_ARGS+=("--model" "$2"); shift 2 ;;
    *) PASS_ARGS+=("$1"); shift ;;
  esac
done

# load repo keys, drop any socks/http proxy (gateways are reached directly)
set -a; [ -f "$ROOT/.env" ] && source "$ROOT/.env"; set +a
unset ALL_PROXY HTTPS_PROXY HTTP_PROXY all_proxy https_proxy http_proxy NO_PROXY no_proxy || true

# Regenerate the live ccr config for the chosen model, then (re)start the router.
"$ROOT/.venv/bin/python" "$HERE/gen_ccr_config.py" "$MODEL" "$CCR_HOME/.claude-code-router/config.json"
node "$HERE/claude-code-router/dist/cli.js" stop  >/dev/null 2>&1 || true
node "$HERE/claude-code-router/dist/cli.js" start >/dev/null 2>&1 &
for i in $(seq 1 20); do
  curl -s -m2 http://127.0.0.1:3456/ -o /dev/null && break || sleep 0.5
done

"$ROOT/.venv/bin/python" "$HERE/run_forecast.py" "${PASS_ARGS[@]}"
