#!/usr/bin/env bash
# Batch driver: start ONE shared adapter, run N questions through run_forecast.py with bounded
# concurrency. Each question is a separate runner process (its own per-question as-of env), but they
# all share the single async adapter on :3456 and the same gateway model. Use for sweeping a
# benchmark file; single-question runs still use run.sh.
#
#   bash agent_sdk/run_batch.sh --model gpt-5.5 --question-file tasks/<file>.jsonl --n 100 --concurrency 5
#   bash agent_sdk/run_batch.sh --run-date 2026-06-30 --as-of 2026-06-29 ...
#
# Per-worker stdout -> log/<run_group>/_batch/<idx>.log ; forecasts -> log/<run_group>/<task>-<model>-tools/.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
export HOME="$HERE/cli_home"
PORT=3456

MODEL="gpt-5.5"
QFILE="tasks/2026-07-06_2026-07-06_futureworld_futurex_UTC+8__question.jsonl"
N=100; CONC=5; START=0; INDICES=""; RUN_DATE=""; AS_OF=""
while [ $# -gt 0 ]; do
  case "$1" in
    --model) MODEL="$2"; shift 2 ;;
    --question-file) QFILE="$2"; shift 2 ;;
    --n) N="$2"; shift 2 ;;
    --concurrency) CONC="$2"; shift 2 ;;
    --start) START="$2"; shift 2 ;;
    --indices) INDICES="$2"; shift 2 ;;   # explicit space-separated list (overrides --start/--n)
    --run-date) RUN_DATE="$2"; shift 2 ;;
    --as-of) AS_OF="$2"; shift 2 ;;
    *) echo "unknown arg: $1"; exit 2 ;;
  esac
done

set -a; [ -f "$ROOT/.env" ] && source "$ROOT/.env"; set +a
unset ALL_PROXY HTTPS_PROXY HTTP_PROXY all_proxy https_proxy http_proxy NO_PROXY no_proxy || true
export FUTURECAST_MODEL="$MODEL"
if [ -n "$RUN_DATE" ]; then
  export FUTURECAST_RUN_DATE="$RUN_DATE"
elif [ -z "${FUTURECAST_RUN_DATE:-}" ]; then
  export FUTURECAST_RUN_DATE="$(date +%F)"
fi
if [ -n "$AS_OF" ]; then
  export FUTURECAST_AS_OF="$AS_OF"
fi
if [ -z "${FUTURECAST_RUN_GROUP:-}" ]; then
  export FUTURECAST_RUN_GROUP="$(date +%Y%m%d-%H%M%S)"
fi
RUN_GROUP="$FUTURECAST_RUN_GROUP"
BATCH_DIR="$ROOT/log/$RUN_GROUP/_batch"; mkdir -p "$BATCH_DIR"

# --- one shared adapter for the whole batch -------------------------------------------------
lsof -ti tcp:$PORT 2>/dev/null | xargs kill -9 2>/dev/null || true
"$ROOT/.venv/bin/python" "$HERE/llm_adapter.py" >"$ROOT/log/adapter.stdout.log" 2>&1 &
ADAPTER_PID=$!
trap 'kill $ADAPTER_PID 2>/dev/null || true' EXIT
for i in $(seq 1 40); do curl -s -m2 "http://127.0.0.1:$PORT/" -o /dev/null && break || sleep 0.5; done
echo "# batch: model=$MODEL n=$N conc=$CONC start=$START qfile=$QFILE run_group=$RUN_GROUP"
echo "# batch cutoff: run_date=$FUTURECAST_RUN_DATE as_of_override=${FUTURECAST_AS_OF:-}"
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
  INDEX_LIST="$(printf '%s\n' $INDICES)"
else
  INDEX_LIST="$(seq "$START" "$((START + N - 1))")"
fi
printf '%s\n' "$INDEX_LIST" | xargs -P "$CONC" -I {} bash -c 'run_one "$@"' _ {}

# --- summary --------------------------------------------------------------------------------
total=0
answered=0
for idx in $INDEX_LIST; do
  total=$((total + 1))
  if grep -E 'answer: .+' "$BATCH_DIR/$idx.log" 2>/dev/null | grep -qv 'answer: None$'; then
    answered=$((answered + 1))
  fi
done
echo "# batch done: $answered/$total produced a non-null answer (see $ROOT/log/$RUN_GROUP/)"
