#!/usr/bin/env bash
# Fixed local entry point — run the forecast agent from THIS repo's own code only.
#
#   bash agent_sdk/run.sh --tools                                  # glm-5, tool-enabled rollout
#   bash agent_sdk/run.sh --model gpt-5.5 --tools                  # gpt-5.5, SAME agent + tools
#   bash agent_sdk/run.sh --model glm-5 --tools \                  # a specific benchmark question
#       --question-file tasks/<file>.jsonl --task-index 0
#
# It (1) starts OUR owned LLM adapter (agent_sdk/llm_adapter.py) — a minimal Anthropic /v1/messages
# endpoint backed by futurecast/llm — then (2) runs the Agent SDK forecast. The Agent SDK harness
# (context/plan/memory/loop) is rented unchanged; only the model-routing layer is ours. HOME is
# redirected into agent_sdk/cli_home so the claude CLI writes its config/state + transcript there
# (the runner copies the transcript into log/).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
export HOME="$HERE/cli_home"             # claude CLI reads config/state + writes transcripts here
PORT=3456

# Parse args: --model NAME selects the route; --tools (and others) are forwarded to the runner.
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

# Start our owned adapter for the chosen model; kill any prior instance on the port.
export FUTURECAST_MODEL="$MODEL"
export FUTURECAST_REASONING_EFFORT="${FUTURECAST_REASONING_EFFORT:-high}"  # adapter reads at boot
lsof -ti tcp:$PORT 2>/dev/null | xargs kill -9 2>/dev/null || true
"$ROOT/.venv/bin/python" "$HERE/llm_adapter.py" >"$ROOT/log/adapter.stdout.log" 2>&1 &
ADAPTER_PID=$!
trap 'kill $ADAPTER_PID 2>/dev/null || true' EXIT
for i in $(seq 1 40); do
  curl -s -m2 "http://127.0.0.1:$PORT/" -o /dev/null && break || sleep 0.5
done

"$ROOT/.venv/bin/python" "$HERE/run_forecast.py" "${PASS_ARGS[@]}"
