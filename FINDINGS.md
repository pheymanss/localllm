# Local LLM coding on a Mac mini M4 (16 GB): findings

Experiments from November 2026: running local models through Ollama as coding agents, measured on the pokegraph spec.
Bottom line: **on 16 GB, today's 4B–9B models cannot build pokegraph on their own.** How the work is set up
(the agent tool, the loop, the sampling settings) changed scores about as much as the choice of model did.
The best setup was a script that runs the test loop while the model only writes code.

## 1. Setup that worked (since deleted)

- **Runtime:** Ollama 0.40.x (MLX runner). Kept only Qwen and MiMo; llama.cpp and oMLX were tried and dropped.
- **Models:** `qwen3.5:9b`, `qwen3.5:4b-mtp-q4_K_M` (4B with multi-token prediction), `mimo-v2.6:9b` (MiMo-V2.6-Distill-Qwen-9B).
- **Context gotcha:** the Ollama app defaults to a 4096-token context and ignores `launchctl setenv` (its setting
  lives in `~/Library/Application Support/Ollama/db.sqlite`, `context_length=0`). That made Claude Code compact
  constantly. Fix: Modelfile variants with `PARAMETER num_ctx`. They share the weight files, so they use no extra disk.
- **Claude Code against Ollama** (`local-claude.sh`, kept in this folder):
  `ANTHROPIC_BASE_URL=http://localhost:11434`, all model env vars set to the local model,
  `CLAUDE_CODE_MAX_OUTPUT_TOKENS=4096`, `CLAUDE_CODE_MAX_CONTEXT_TOKENS=<real ctx>`,
  `CLAUDE_CODE_AUTO_COMPACT_WINDOW=100000` (100K is the minimum Claude Code accepts; lower values warn).
- **Sampling matters:** the stock `mimo-v2.6:9b` ships with `presence_penalty 0` and `repeat_penalty 1`, and it got
  stuck in thinking loops of 40–50K characters. Adding `PARAMETER presence_penalty 1.5` (Qwen's own advice, and the
  4B's default) fixed it. See `Modelfile.mimo`.

### Context sweep (filled to about 90%; prefill/decode tok/s, minimum free memory, swap)

| Model | 32K | 48K | 64K | 96K | 128K |
|---|---|---|---|---|---|
| qwen3.5:4b-mtp | 238/22, 37% | – | 156/17, 13%, 0.3 GB swap | 117/15, 17% | 118/12, 5%, 1.8 GB swap |
| qwen3.5:9b | 204/13, 9% | 180/12, 14%, 0.6 GB | 161/10, 6%, 1.9 GB | crashed (HTTP 500, 4 GB swap) | – |
| mimo-v2.6:9b | 208/13, 20% | 193/11, 6%, 0.6 GB | 163/10, 4%, 2 GB | – | – |

Chosen sizes: **48K for the 9B models, 64K for the 4B.**

## 2. Benchmark (`pokegraph-bench/`)

Five tasks cut from `POKEGRAPH_SPEC.md`, each with its own TASK.md, a pre-built Kuzu graph where needed, and hidden
pytest tests (96 in total) that pass 100% against the reference implementation in `ref/`:

| Task | What it asks | Tests |
|---|---|---|
| t1_stats | stat formula, natures, boosts | 27 |
| t2_etl | ETL CLI from Showdown `raw/*.js` files | 7 |
| t4_types | type matchup + coverage over the graph | 18 |
| t5_speed | speed check (items, paralysis, ties) | 19 |
| t6_damage | damage calculator | 25 |

Every run: 20-minute hard limit per task (`hardcap.pl` kills the whole process group), graded with the hidden tests.
Spec issues found along the way: §7 says Stone Edge vs Skarmory is 2×, but it is 1× (Fire Punch is the 2× move).
Showdown's client data has no desc/shortDesc fields, which breaks Sheer Force detection.

## 3. Results: hidden tests passed (one run per cell)

| Setup | Model | t1 /27 | t2 /7 | t4 /18 | t5 /19 | t6 /25 | Total /96 |
|---|---|---|---|---|---|---|---|
| Claude Code, tests hidden | 4B | 19 | 0 | 0 | 0 | 0 | 19 |
| | mimo | 17 | 0 | 0 | 2 | 0 | 19 |
| Claude Code, tests visible | 4B | 21 | 0 | 16 | 0 | 0 | 37 |
| | mimo | 16 | 0 | **18** | 0 | 0 | 34 |
| pi (plain) | 4B | 22 | 0 | 0 | 12 | 1 | 35 |
| | mimo | 0 | 0 | 0 | 0 | 0 | 0 |
| pi + Level 1 fixes | 4B | 15 | 0 | **18** | 0 | 2 | 35 |
| | mimo | **26** | 0 | 4 | 0 | 0 | 30 |
| **Level 3 (script runs the loop)** | **4B** | **25** | **2** | 4 | **17** | 0 | **48** |
| | mimo | **26** | 0 | 4 | 2 | 0 | 32 |

Raw data: `results.jsonl` (CC, tests hidden), `results_visible.jsonl`, `results_pi.jsonl`, `results_l1.jsonl`,
`results_l3.jsonl`. `results_l3_v1.jsonl` is a broken first Level 3 run: mimo's replies were tool calls that the script didn't read.
Code and logs for every run are in `runs/`.

**Caveat:** single runs and high variance. The 4B scored 0, 16, 18 and 4 on t4 across setups. Only big jumps count.

## 4. What we learned

1. **The agent tool matters a lot for small models.** Claude Code sends roughly 15–20K tokens of system prompt and tools. At about
   190 tok/s prefill, each cache miss costs mimo 1–2 minutes (it made only 5 tool calls in 20 minutes). pi's prompt is about 2K.
2. **Visible acceptance tests help** (Claude Code total: 19 → 37 and 19 → 34), but they aren't enough on their own.
3. **Mimo: careful but slow, and prone to thinking loops** without a presence penalty. When it finishes, the code is right
   (types 18/18, stats 26/27). It is so tuned for agent work that it answers with tool calls even when no tools are offered,
   so always give it real tools.
4. **4B: fast but sloppy.** 20–25% of its tool calls fail, it makes logic slips (a reversed nature table), and `iv=None`
   isn't handled. It does best when a script supplies the loop and checks its work.
5. **Tool output floods the context.** Full pytest dumps of 27K characters filled the 4B's 64K window. Use `--tb=line` or `--tb=short`.
6. **Recalling game data from memory is the main reasoning failure** (natures, type chart). Giving the model a lookup tool and the rule
   "look it up, don't recall it" helps.
7. **Keep the best version.** Runs often reached a good state and then broke it before the deadline. Snapshot on every improvement
   (`best_keeper.py`, built into `tdd_loop.py`).
8. **A script-driven loop beats letting the model run the loop** (`tdd_loop.py`). Each step is a fresh, short request with one failing
   test, `run_python` and `write_file` tools, and a change is kept only if the score improves. Thinking is off on the first try and on
   for retries, and runaway thinking gets "budget forcing": stop it, keep the end of the reasoning, and demand an answer.
   Result: the 4B's best total (48/96), its first ETL passes, and speed 17/19.
9. **Damage calc (t6) stayed at 0 everywhere.** In Level 3 both models kept looking things up and never wrote the file
   (78 lookups for mimo).
10. **Not worth it here:** Qwen2.5-Coder (older, with unreliable tool calls in agent loops; the 14B doesn't fit with real context).
    Hermes Agent (a general assistant, not a lean coding agent). Qwen3-Coder-30B-A3B (about 18 GB at 4-bit, too big for 16 GB).

**Practical advice today:** use cloud Claude to build things. Local models are worth it only for small, well-scoped edits
or autocomplete.

## 5. Next steps (when better models arrive)

Start by re-running the benchmark exactly as is, to get a baseline for the new model.

1. **Force a write in `tdd_loop.py`:** after 3 lookups, drop the `run_python` tool so the model has to call `write_file`. This is the likely fix for t6.
2. **Split big tasks into steps:** a cloud model splits t6/t2 into 3–4 small functions with their own small tests, and the local
   model fills each one in through the Level 3 loop.
3. **Repeat runs:** 3 runs per setup, reporting the median, so the scores mean something.
4. **Escalate to the cloud:** after N local failures on one test, hand that test to cloud Claude. Measure the cost per task solved.
5. **Level 2 proxy (optional):** a small server in front of Ollama that adds thinking budgets, loop detection with nudges, and
   tool-call repair for any agent tool (Claude Code, pi, opencode).
6. **opencode** as another agent tool to compare against pi (it uses per-model prompts).
7. **Models to watch:** anything around 8–14B dense or around 20–30B MoE that fits in about 12 GB at 4-bit with strong tool calling. Retest the
   context sweep (`num_ctx` vs free memory) for each new model before the benchmark.

## 6. How to re-run

```bash
cd pokegraph-bench
./setup.sh             # venv, knowledge JSON and the Kuzu graph (left out of git; rebuilt from raw/)
ollama pull <model>    # then create a <model>-48k variant with PARAMETER num_ctx (and presence_penalty if it loops)
./ladder_l3.sh <model>-48k                  # Level 3, writes results_l3.jsonl
./ladder_l1.sh <model>-48k                  # Level 1 (needs pi: npm i -g @mariozechner/pi-coding-agent, plus ~/.pi/agent/models.json)
TASKSET=tasks_visible RESULTS=r.jsonl ./ladder.sh <model>-48k   # Claude Code
```

- **Run folders:** the ladders work in `/tmp/pg-cc`, `/tmp/pg-pi`, `/tmp/pg` and `/tmp/pg3` (short paths on purpose).
- **Folders:** `ref/` is the reference implementation (rebuild the graph with `ref/graph/load.py`), `hidden/` holds the grading
  tests, `tasks*/` are the task variants, and `FAKE_REF=ref/query python tdd_loop.py ...` checks the loop without a model.
- **pi needs:** stdin closed (`</dev/null`) in non-interactive mode, otherwise it hangs.

## 7. Cleanup done (2026-11-15)

Removed: all Ollama models (about 19 GB), `~/.local/bin/local-claude`, the broken `~/.local/bin/omlx` link, the pi agent and
`~/.pi`, Node.js (installed only for pi), the benchmark venv and temporary run folders.
Ollama itself was then uninstalled too (the app, `~/.ollama`, and its Application Support, cache, preferences and WebKit data).
To start again: install Ollama from ollama.com, then follow §1 (context variants) and §6.
