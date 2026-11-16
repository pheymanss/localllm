#!/bin/zsh
# Same as ladder.sh, but drives the pi agent instead of Claude Code.
# usage: ladder_pi.sh <ollama-model> [tasks...]   env: TASKSET, RESULTS, PROMPT
P=${0:a:h}; M=$1; shift; L=${M//[:\/]/_}
TASKS=($@); (( $#TASKS )) || TASKS=(t1_stats t2_etl t4_types t5_speed t6_damage)
TASKSET=${TASKSET:-tasks_visible}; RESULTS=${RESULTS:-results_pi.jsonl}
export PATH=$P/venv/bin:$PATH PI_OFFLINE=1
RUNS=/tmp/pg-pi; mkdir -p $RUNS
for T in $TASKS; do
  W=$RUNS/pi_${TASKSET}_${L}_$T; rm -rf $W; cp -R $P/$TASKSET/$T $W
  t0=$(date +%s)
  ( cd $W && $P/hardcap.pl 1200 pi --offline --no-session --provider ollama --model "$M" --mode json -p "$PROMPT" </dev/null > $W.log.jsonl 2> $W.err )
  dt=$(( $(date +%s) - t0 ))
  cp $P/hidden/conftest.py $P/hidden/test_h_$T.py $W/
  HID=$(cd $W && perl -e 'alarm 900; exec @ARGV' python -m pytest -q -p no:cacheprovider test_h_$T.py 2>&1 | tail -1)
  OWN=$(cd $W && [ -d tests ] && perl -e 'alarm 600; exec @ARGV' python -m pytest -q -p no:cacheprovider tests 2>&1 | tail -1 || echo "no own tests")
  python3 - "$M" "$T" "$dt" "$HID" "$OWN" "$W.log.jsonl" "$TASKSET" <<'PY' | tee -a $P/$RESULTS
import json, sys, re
m, t, dt, hid, own, log, ts = sys.argv[1:]
turns = calls = errs = compacts = 0; end = None; maxin = 0
for l in open(log, errors="replace"):
    try: e = json.loads(l)
    except Exception: continue
    ty = e.get("type")
    if ty == "turn_start": turns += 1
    elif ty == "tool_execution_end": calls += 1; errs += bool(e.get("isError"))
    elif ty and "compact" in ty: compacts += 1
    elif ty == "agent_end": end = "done"
    elif ty == "message_end":
        u = (e.get("message") or {}).get("usage") or {}
        maxin = max(maxin, (u.get("input") or 0) + (u.get("cacheRead") or 0))
p = re.search(r"(\d+) passed", hid); f = re.search(r"(\d+) (failed|error)", hid)
passed = int(p.group(1)) if p else 0; failed = int(f.group(1)) if f else 0
print(json.dumps({"agent": "pi", "taskset": ts, "model": m, "task": t, "secs": int(dt), "hidden_pass": passed, "hidden_total": passed + failed,
  "hidden_raw": hid[:120], "own_tests": own[:80], "turns": turns, "tool_calls": calls, "tool_errors": errs, "max_ctx": maxin,
  "end": end or "timeout/killed", "compactions": compacts}))
PY
done
ollama stop $M
