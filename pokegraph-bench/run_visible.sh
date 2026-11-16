#!/bin/zsh
cd ${0:a:h}
export TASKSET=tasks_visible RESULTS=results_visible.jsonl
export PROMPT="Read TASK.md in this directory. The acceptance tests in tests/test_given.py are already written: make all of them pass without editing them. Start by reading TASK.md and tests/test_given.py, then implement, run python -m pytest -q tests/test_given.py, and fix your code until every test passes. When finished, reply with a one-paragraph summary."
./ladder.sh qwen3.5:4b-mtp-q4_K_M-64k
./ladder.sh mimo-v2.6:9b-48k
echo ALL DONE
