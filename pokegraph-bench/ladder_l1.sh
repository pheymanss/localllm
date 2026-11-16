#!/bin/zsh
# Level 1: pi + short paths + compact pytest output + look-it-up prompt + keep-best snapshots.
# usage: ladder_l1.sh <ollama-model> [tasks...]
P=${0:a:h}; M=$1; shift; L=${M//[:\/]/_}
TASKS=($@); (( $#TASKS )) || TASKS=(t1_stats t2_etl t4_types t5_speed t6_damage)
TASKSET=tasks_l1; RESULTS=${RESULTS:-results_l1.jsonl}
PROMPT=${PROMPT:-"Read TASK.md in this directory. The acceptance tests in tests/test_given.py are already written: make all of them pass without editing them. Start by reading TASK.md and tests/test_given.py, then implement, run python -m pytest tests/test_given.py, and fix your code until every test passes. Rules: work only inside this directory and use relative paths. Never recall game data (natures, type chart, base stats, move data) from memory: look it up in the data files or the graph with a quick query. If you are unsure about something, check it with a tool instead of deliberating. When finished, reply with a one-paragraph summary."}
export PATH=$P/venv/bin:$PATH PI_OFFLINE=1
RUNS=/tmp/pg; mkdir -p $RUNS
for T in $TASKS; do
  W=$RUNS/${L}_$T; B=$W.best; rm -rf $W $B $W.stop; cp -R $P/$TASKSET/$T $W
  python $P/best_keeper.py $W $P/$TASKSET/$T $P/hidden/test_h_$T.py $P/hidden/conftest.py $B & KP=$!
  t0=$(date +%s)
  ( cd $W && $P/hardcap.pl 1200 pi --offline --no-session --provider ollama --model "$M" --mode json -p "$PROMPT" </dev/null > $W.log.jsonl 2> $W.err )
  dt=$(( $(date +%s) - t0 ))
  touch $W.stop; wait $KP
  cp $P/hidden/conftest.py $P/hidden/test_h_$T.py $W/
  FIN=$(cd $W && perl -e 'alarm 900; exec @ARGV' python -m pytest -q -p no:cacheprovider -o addopts= test_h_$T.py 2>&1 | tail -1)
  python3 - "$M" "$T" "$dt" "$FIN" "$W.log.jsonl" "$B/best.json" <<'PY' | tee -a $P/$RESULTS
import json, sys, re
m, t, dt, fin, log, bestf = sys.argv[1:]
turns = calls = errs = 0; end = None; maxin = 0; maxthink = 0
for l in open(log, errors="replace"):
    try: e = json.loads(l)
    except Exception: continue
    ty = e.get("type")
    if ty == "turn_start": turns += 1
    elif ty == "tool_execution_end": calls += 1; errs += bool(e.get("isError"))
    elif ty == "agent_end": end = "done"
    elif ty == "message_end":
        msg = e.get("message") or {}; u = msg.get("usage") or {}
        maxin = max(maxin, (u.get("input") or 0) + (u.get("cacheRead") or 0))
        maxthink = max(maxthink, sum(len(c.get("thinking", "")) for c in msg.get("content", []) if c.get("type") == "thinking"))
p = re.search(r"(\d+) passed", fin); f = re.search(r"(\d+) (failed|error)", fin)
fp = int(p.group(1)) if p else 0
try: b = json.load(open(bestf))
except Exception: b = {"pass": 0, "total": 0, "at": None, "checks": 0}
print(json.dumps({"agent": "pi-l1", "model": m, "task": t, "secs": int(dt), "best_pass": max(b["pass"], 0), "best_total": b["total"], "best_at": b["at"],
  "final_pass": fp, "final_raw": fin[:100], "checks": b["checks"], "turns": turns, "tool_calls": calls, "tool_errors": errs,
  "max_ctx": maxin, "max_think_chars": maxthink, "end": end or "timeout/killed"}))
PY
done
ollama stop $M
