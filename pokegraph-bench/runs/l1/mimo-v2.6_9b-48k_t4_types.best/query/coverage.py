"""Coverage of a move list against a target Pokemon."""
from kuzu_conn import query, get_conn

def coverage(move_list, target_id) -> dict:
    conn = get_conn()
    types = query('MATCH (p:Pokemon {id:$id})-[:HAS_TYPE]->(t:Type) RETURN t.name ORDER BY p.id',
                  {"id": target_id})

    by_move = {}
    for mid in move_list:
        rows = query('MATCH (m:Move {id:$id}) RETURN m.type, m.category, m.base_power', {"id": mid})
        if not rows:
            by_move[mid] = {"mult": None, "error": "move not found"}
            continue

        mtype, category, _power = rows[0]
        if category == 'status':
            by_move[mid] = {"move_type": mtype, "mult": None, "status_move": True}
            continue

        # product of EFFECTIVE_VS over the target's types; missing edges mean 1x
        mults = []
        for t in types:
            rows = query('MATCH (a:Type {name:$a})-[e:EFFECTIVE_VS]->(b:Type {name:$b}) RETURN e.multiplier',
                         {"a": mtype, "b": t})
            if rows:
                mults.append(rows[0][0])
        by_move[mid] = {"mult": 1.0}
        for m in mults:
            by_move[mid]["mult"] *= m

    best_mult = None
    best_moves = []
    for mid, entry in by_move.items():
        mult = entry.get("mult")
        if not isinstance(mult, float):
            continue
        if best_mult is None or mult > best_mult:
            best_mult = mult
            best_moves = [mid]
        elif mult == best_mult:
            best_moves.append(mid)

    return {"best_mult": best_mult, "best_moves": sorted(best_moves), "by_move": by_move}