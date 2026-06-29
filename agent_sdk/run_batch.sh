#!/usr/bin/env bash
# Batch driver: start ONE shared adapter, run N questions through run_forecast.py with bounded
# concurrency. Each question is a separate runner process (its own per-question as-of env), but they
# all share the single async adapter on :3456 and the same gateway model. Use for sweeping a
# benchmark file; single-question runs still use run.sh.
#
#   bash agent_sdk/run_batch.sh --model gpt-5.5 --question-file tasks/<file>.jsonl --n 100 --concurrency 5
#
# Per-worker stdout -> log/<run_group>/_batch/<idx>.log ; forecasts -> log/<run_group>/<task>-<model>-tools/.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
export HOME="$HERE/cli_home"
PORT=3456

MODEL="gpt-5.5"
QFILE="tasks/2026-07-06_2026-07-06_futureworld_futurex_UTC+8__question.jsonl"
N=100; CONC=5; START=0; INDICES=""
while [ $# -gt 0 ]; do
  case "$1" in
    --model) MODEL="$2"; shift 2 ;;
    --question-file) QFILE="$2"; shift 2 ;;
    --n) N="$2"; shift 2 ;;
    --concurrency) CONC="$2"; shift 2 ;;
    --start) START="$2"; shift 2 ;;
    --indices) INDICES="$2"; shift 2 ;;   # explicit space-separated list (overrides --start/--n)
    *) echo "unknown arg: $1"; exit 2 ;;
  esac
done

set -a; [ -f "$ROOT/.env" ] && source "$ROOT/.env"; set +a
unset ALL_PROXY HTTPS_PROXY HTTP_PROXY all_proxy https_proxy http_proxy NO_PROXY no_proxy || true
export FUTURECAST_MODEL="$MODEL"
RUN_GROUP="${FUTURECAST_RUN_GROUP:-futureworld-0629}"
BATCH_DIR="$ROOT/log/$RUN_GROUP/_batch"; mkdir -p "$BATCH_DIR"

# --- one shared adapter for the whole batch -------------------------------------------------
lsof -ti tcp:$PORT 2>/dev/null | xargs kill -9 2>/dev/null || true
"$ROOT/.venv/bin/python" "$HERE/llm_adapter.py" >"$ROOT/log/adapter.stdout.log" 2>&1 &
ADAPTER_PID=$!
trap 'kill $ADAPTER_PID 2>/dev/null || true' EXIT
for i in $(seq 1 40); do curl -s -m2 "http://127.0.0.1:$PORT/" -o /dev/null && break || sleep 0.5; done
echo "# batch: model=$MODEL n=$N conc=$CONC start=$START qfile=$QFILE run_group=$RUN_GROUP"
echo "# adapter pid=$ADAPTER_PID; per-worker logs -> $BATCH_DIR/<idx>.log"

# --- one worker = one question (own process, own as-of env), shared adapter -----------------
run_one() {
  local idx="$1" log="$BATCH_DIR/$1.log"
  if "$ROOT/.venv/bin/python" "$HERE/run_forecast.py" --tools --model "$MODEL" \
       --question-file "$QFILE" --task-index "$idx" >"$log" 2>&1; then
    echo "[ok]   idx=$idx $(grep -oE 'answer: .*' "$log" | tail -1)"
  else
    echo "[FAIL] idx=$idx (see $log: $(tail -1 "$log"))"
  fi
}
export -f run_one; export ROOT HERE MODEL QFILE BATCH_DIR

if [ -n "$INDICES" ]; then
  printf '%s\n' $INDICES | xargs -P "$CONC" -I {} bash -c 'run_one "$@"' _ {}
else
  seq "$START" "$((START + N - 1))" | xargs -P "$CONC" -I {} bash -c 'run_one "$@"' _ {}
fi

# --- summary --------------------------------------------------------------------------------
ok=$(grep -lh '' "$BATCH_DIR"/*.log 2>/dev/null | wc -l | tr -d ' ')
answered=$(grep -rhoE '"answer": "?[^",]' "$ROOT/log/$RUN_GROUP"/*-tools/result.json 2>/dev/null | grep -cv 'null')
echo "# batch done: $answered/$N produced a non-null answer (see $ROOT/log/$RUN_GROUP/)"
