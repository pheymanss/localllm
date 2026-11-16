#!/bin/zsh
# Level 3: script-driven test loop (tdd_loop.py). Same tasks, 20-minute budget, graded on the best kept version.
# usage: ladder_l3.sh <ollama-model> [tasks...]
P=${0:a:h}; M=$1; shift; L=${M//[:\/]/_}
TASKS=($@); (( $#TASKS )) || TASKS=(t1_stats t2_etl t4_types t5_speed t6_damage)
RESULTS=${RESULTS:-results_l3.jsonl}; export PATH=$P/venv/bin:$PATH
RUNS=/tmp/pg3; mkdir -p $RUNS
for T in $TASKS; do
  W=$RUNS/${L}_$T; rm -rf $W $W.l3best $W.l3.jsonl $W.grade; cp -R $P/tasks_l1/$T $W
  t0=$(date +%s)
  OUT=$($P/hardcap.pl 1320 python $P/tdd_loop.py "$M" $W --budget 1200 --log $W.l3.jsonl 2>$W.err | tail -1)
  dt=$(( $(date +%s) - t0 ))
  cp -R $P/tasks_l1/$T $W.grade; rm -rf $W.grade/query; cp -R $W.l3best $W.grade/query
  cp $P/hidden/conftest.py $P/hidden/test_h_$T.py $W.grade/
  HID=$(cd $W.grade && perl -e 'alarm 900; exec @ARGV' python -m pytest -q -p no:cacheprovider -o addopts= test_h_$T.py 2>&1 | tail -1)
  python3 - "$M" "$T" "$dt" "$HID" "$W.l3.jsonl" <<'PY' | tee -a $P/$RESULTS
import json, sys, re, collections
m, t, dt, hid, log = sys.argv[1:]
c = collections.Counter(); forced = 0; thinkmax = 0
for l in open(log, errors="replace"):
    try: e = json.loads(l)
    except Exception: continue
    c[e["ev"]] += 1
    if e["ev"] == "reply": c["kind_" + e["kind"]] += 1
    if e["ev"] == "llm": thinkmax = max(thinkmax, e.get("think_chars", 0)); c["how_" + e["how"][:9]] += 1
p = re.search(r"(\d+) passed", hid); f = re.search(r"(\d+) (failed|error)", hid)
passed = int(p.group(1)) if p else 0
print(json.dumps({"agent": "l3", "model": m, "task": t, "secs": int(dt), "hidden_pass": passed, "hidden_total": passed + (int(f.group(1)) if f else 0),
  "hidden_raw": hid[:100], "llm_calls": c["llm"], "forced": c["llm_forced"], "accepts": c["accept"], "rejects": c["reject"],
  "probes": c["kind_probe"], "no_file": c["kind_none"], "think_caps": c["how_think_cap"], "time_caps": c["how_time_cap"], "max_think_chars": thinkmax}))
PY
done
ollama stop $M
