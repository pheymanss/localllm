"""Coverage of a move list against a target Pokemon (spec section 7)."""
from kuzu_conn import query
from type_matchup import target_types, type_matchup

def coverage(move_list, target_id):
    """Return coverage of each move in `move_list` against Pokemon `target_id`.

    Status moves are reported but excluded from the best; unknown moves are
    reported with an error and excluded from the best.
    """
    by_move = {}
    best_mult = None
    best_moves = []

    for mid in move_list:
        rows = query(
            """
            MATCH (m:Move {id:$mid})-[:IS_TYPE]->(t:Type)
            RETURN m.name AS name, t.name AS type, m.category AS category, m.base_power AS power
            """,
            {"mid": mid},
        )
        if not rows:
            by_move[mid] = {"mult": None, "error": "move not found"}
            continue

        move_type = category = power = None
        for name, tname, cat, pw in rows:
            move_type, category, power = tname, cat, pw
        if category == "status":
            by_move[mid] = {"move_type": move_type, "mult": None, "status_move": True}
            continue

        mult = type_matchup(move_type, target_id)
        by_move[mid] = {"move_type": move_type, "mult": mult, "status_move": False}
        if best_mult is None or mult > best_mult:
            best_mult = mult
            best_moves = [mid]
        elif mult == best_mult:
            best_moves.append(mid)

    return {
        "best_mult": best_mult,
        "best_moves": sorted(best_moves),
        "by_move": by_move,
    }