"""Coverage calculation (spec section 7)."""
from type_matchup import type_matchup


def coverage(move_list, target_id):
    """Calculate move coverage against a target.
    
    Args:
        move_list: list of move ids to check
        target_id: pokemon id string
        
    Returns:
        dict with "best_mult", "best_moves", and "by_move" keys
    """
    # Get target's types
    result = type_matchup(target_id)
    
    by_move = {}
    best_mult = None
    best_moves = []
    
    for move_id in move_list:
        # Get move details
        rows = query(cypher=f"""MATCH (m:Move {{id:$id}})-[r:IS_TYPE]->(t:Type) RETURN m, t.type""", params={"id": move_id})
        
        if not rows or len(rows) == 0:
            by_move[move_id] = {"mult": None, "error": "move not found"}
            continue
        
        move_row = rows[0]
        move_type = move_row[1]
        category = move_row[0][0].get("category") if isinstance(move_row[0], list) else move_row[0].get("category")
        
        # Check if status move
        is_status_move = False
        if category == "status":
            is_status_move = True
            by_move[move_id] = {"move_type": move_type, "mult": None, "status_move": True}
        elif category == "physical" or category == "special":
            # Calculate type effectiveness
            mult = 1.0
            if result:
                for defender_type in result:
                    eff_rows = query(cypher=f"""MATCH (a:Type {{name:$atk}})-[e:EFFECTIVE_VS]->(d:Type {{name:$def}}) RETURN e.multiplier""", 
                                   params={"atk": move_type, "def": defender_type})
                    if eff_rows:
                        mult *= eff_rows[0][0]
            
            by_move[move_id] = {"mult": mult}
            
            if best_mult is None or mult > best_mult:
                best_mult = mult
                best_moves = [move_id]
            elif mult == best_mult:
                best_moves.append(move_id)
        else:
            # Unknown category, treat as error
            by_move[move_id] = {"mult": None, "error": "unknown category"}
    
    return {
        "best_mult": best_mult,
        "best_moves": best_moves,
        "by_move": by_move
    }


def query(cypher, params=None):
    """Run a Cypher query (helper for coverage)."""
    from kuzu_conn import query as run_query
    return run_query(cypher, params)
