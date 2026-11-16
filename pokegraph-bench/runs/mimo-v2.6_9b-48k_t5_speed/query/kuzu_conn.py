"""Shared read-only Kuzu connection cache (spec section 4, simplified)."""
import os, re, threading
from pathlib import Path
import kuzu
LOCK = threading.RLock()
ROOT = Path(__file__).resolve().parents[1]
ALIASES = {k: "gen9" for k in ["gen9","gen9ou","gen9uu","gen9ru","gen9nu","gen9ubers","gen9lc","gen9vgc","gen9bss","gen9doubles"]}
class DatabaseMissing(RuntimeError): pass
_cache = {}
def resolve_path(key=None):
    key = key or os.environ.get("POKEGRAPH_DB", "gen9ou")
    if re.search(r"[/\\.:]", key): raise ValueError(f"invalid db key: {key}")
    p = ROOT / "graph" / f"{ALIASES.get(key, key)}.db"
    if not p.exists(): raise DatabaseMissing(f"{p} not found. Build it with: uv run graph/load.py --db {ALIASES.get(key, key)}")
    return p
def get_conn(key=None):
    p = resolve_path(key)
    with LOCK:
        if p not in _cache:
            _cache[p] = kuzu.Connection(kuzu.Database(str(p), read_only=True))
        return _cache[p]
def query(cypher, params=None, key=None):
    """Run a query and return all rows as a list of lists."""
    conn = get_conn(key)
    with LOCK:
        res = conn.execute(cypher, params or {})
        rows = []
        while res.has_next(): rows.append(res.get_next())
        return rows
