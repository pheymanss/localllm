# Can a 16 GB Mac mini be your coding agent?

I benchmarked small local models (Qwen3.5 4B/9B, MiMo-V2.6 9B on Ollama) as autonomous coding agents on a
Mac mini M4 with 16 GB. The test: implementing pieces of a Pokémon battle-data graph project (pokegraph), graded by
96 hidden tests. Same models, five setups:

| Setup | Qwen3.5 4B | MiMo 9B |
|---|---|---|
| Claude Code, tests hidden | 19 / 96 | 19 / 96 |
| Claude Code, tests visible | 37 | 34 |
| pi agent | 35 | 0 (endless thinking loops) |
| pi + fixes (sampling, compact output, keep best) | 35 | 30 |
| **Script-driven test loop** ([`tdd_loop.py`](pokegraph-bench/tdd_loop.py)) | **48** | 32 |

**Takeaways:**
- How the work is set up changed scores about as much as the choice of model.
- A script that runs the loop, giving the model one failing test per fresh, short request, beat full agent tools for the small model.
- None of the setups could finish the damage calculator.

Full write-up, including the context-size sweep, failure modes and next steps: **[FINDINGS.md](FINDINGS.md)**.

## Layout

- `FINDINGS.md`: results, lessons, next steps
- `local-claude.sh`: run Claude Code against a local Ollama model, with sensible context and compaction settings
- `Modelfile.mimo`: MiMo with 48K context and the presence penalty that stops its thinking loops
- `pokegraph-bench/`
  - `tasks*/`: the five task variants
  - `hidden/`: grading tests
  - `ref/`: reference implementation
  - `ladder*.sh`: runners for each setup
  - `tdd_loop.py`: script-driven loop
  - `best_keeper.py`: keeps the best-scoring version during a run
  - `results_*.jsonl`: raw scores
  - `runs/`: code and logs for each run

Reproduce with `cd pokegraph-bench && ./setup.sh`, then follow §6 of FINDINGS.md.
