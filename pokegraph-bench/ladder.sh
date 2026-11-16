#!/bin/zsh
# usage: ladder.sh <model-with-size-suffix> [tasks...]
P=${0:a:h}; M=$1; shift; L=${M//[:\/]/_}
TASKS=($@); (( $#TASKS )) || TASKS=(t1_stats t2_etl t4_types t5_speed t6_damage)
CTX=$(( ${${M##*-}%k} * 1024 ))
TASKSET=${TASKSET:-tasks}; RESULTS=${RESULTS:-results.jsonl}
PROMPT=${PROMPT:-"Read TASK.md in this directory and complete the task it describes. Work step by step: implement, write your own tests, run them with python -m pytest -q, and fix failures until they pass. When finished, reply with a one-paragraph summary."}
export PATH=$P/venv/bin:$PATH
export ANTHROPIC_BASE_URL=http://localhost:11434 ANTHROPIC_AUTH_TOKEN=ollama ANTHROPIC_API_KEY="" ANTHROPIC_MODEL=$M
export ANTHROPIC_DEFAULT_OPUS_MODEL=$M ANTHROPIC_DEFAULT_SONNET_MODEL=$M ANTHROPIC_DEFAULT_HAIKU_MODEL=$M CLAUDE_CODE_SUBAGENT_MODEL=$M
export CLAUDE_CODE_MAX_OUTPUT_TOKENS=4096 CLAUDE_CODE_MAX_CONTEXT_TOKENS=$CTX CLAUDE_CODE_AUTO_COMPACT_WINDOW=100000
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 API_TIMEOUT_MS=3000000 CLAUDE_CODE_ATTRIBUTION_HEADER=0 CLAUDE_CONFIG_DIR=$P/ccconfig
unset CLAUDECODE CLAUDE_CODE_ENTRYPOINT CLAUDE_CODE_SSE_PORT
RUNS=/tmp/pg-cc; mkdir -p $RUNS
for T in $TASKS; do
  W=$RUNS/${TASKSET}_${L}_$T; rm -rf $W; cp -R $P/$TASKSET/$T $W
  t0=$(date +%s)
  ( cd $W && $P/hardcap.pl 1200 claude -p "$PROMPT" \
      --allowedTools "Read,Edit,Write,Bash,Glob,Grep" --permission-mode acceptEdits --max-turns 40 --output-format stream-json --verbose > $W.log.jsonl 2> $W.err )
  dt=$(( $(date +%s) - t0 ))
  cp $P/hidden/conftest.py $P/hidden/test_h_$T.py $W/
  HID=$(cd $W && perl -e 'alarm 900; exec @ARGV' python -m pytest -q -p no:cacheprovider test_h_$T.py 2>&1 | tail -1)
  OWN=$(cd $W && [ -d tests ] && ls tests/*.py >/dev/null 2>&1 && perl -e 'alarm 600; exec @ARGV' python -m pytest -q -p no:cacheprovider tests 2>&1 | tail -1 || echo "no own tests")
  python3 - "$M" "$T" "$dt" "$HID" "$OWN" "$W.log.jsonl" <<'PY' | tee -a $P/$RESULTS
import json, sys, re
m, t, dt, hid, own, log = sys.argv[1:]
turns = None; reason = None; compacts = 0; err = None; out_tok = 0
for l in open(log, errors="replace"):
    try: e = json.loads(l)
    except Exception: continue
    if e.get("type") == "system" and e.get("subtype") == "compact_boundary": compacts += 1
    if e.get("type") == "result": turns = e.get("num_turns"); reason = e.get("subtype"); err = e.get("is_error"); out_tok = (e.get("usage") or {}).get("output_tokens")
p = re.search(r"(\d+) passed", hid); f = re.search(r"(\d+) (failed|error)", hid)
passed = int(p.group(1)) if p else 0; failed = int(f.group(1)) if f else 0
print(json.dumps({"taskset": __import__("os").environ.get("TASKSET","tasks"), "model": m, "task": t, "secs": int(dt), "hidden_pass": passed, "hidden_total": passed + failed, "hidden_raw": hid[:120],
  "own_tests": own[:80], "turns": turns, "end": reason or "timeout/killed", "compactions": compacts}))
PY
done
ollama stop $M
