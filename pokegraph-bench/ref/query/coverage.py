from kuzu_conn import query
from type_matchup import _types, _mult
def coverage(move_list, target_id):
    types = _types(target_id); by = {}
    for mid in move_list:
        r = query("MATCH (m:Move {id:$id}) RETURN m.type, m.category", {"id": mid})
        if not r: by[mid] = {"mult": None, "error": "move not found"}; continue
        t, c = r[0]
        if c == "status": by[mid] = {"move_type": t, "mult": None, "status_move": True}; continue
        by[mid] = {"move_type": t, "mult": _mult(t, types)}
    dmg = {k: v["mult"] for k, v in by.items() if v.get("mult") is not None}
    best = max(dmg.values()) if dmg else None
    return {"best_mult": best, "best_moves": [k for k, v in dmg.items() if v == best], "by_move": by}
