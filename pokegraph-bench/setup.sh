#!/bin/zsh
# Recreate everything that is left out of git: the Python venv, the knowledge JSON, and the Kuzu graph
# that tasks t4–t6 need. usage: ./setup.sh   (needs uv: https://docs.astral.sh/uv/)
set -e; cd ${0:a:h}
[[ -x venv/bin/python ]] || { uv venv -q -p 3.13 venv && uv pip install -q -p venv kuzu json5 pytest; }
venv/bin/python ref/query/etl.py raw ref/knowledge
venv/bin/python ref/graph/load.py ref/knowledge ref/graph/gen9.db
for set in tasks tasks_visible tasks_l1; do for t in t4_types t5_speed t6_damage; do
  mkdir -p $set/$t/graph && cp ref/graph/gen9.db $set/$t/graph/gen9.db
done; done
echo "setup done: venv, ref/knowledge, ref/graph/gen9.db and task graphs are ready"
