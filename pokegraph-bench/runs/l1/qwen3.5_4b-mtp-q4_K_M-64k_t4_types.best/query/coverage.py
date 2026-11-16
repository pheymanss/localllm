"""coverage: Calculate move coverage against a target."""

# Import from sibling module (kuzu_conn is in same directory)
from kuzu_conn import query


def coverage(move_list, target_id):
    """
    Calculate move coverage against target_id.
    
    Args:
        move_list: List of move IDs (e.g., ["earthquake", "stoneedge"])
        target_id: The target Pokemon name
        
    Returns:
        dict with keys:
            - best_mult: float or None (highest multiplier for damaging moves)
            - best_moves: list of move IDs that achieve best_mult
            - by_move: dict of {move_id: {"move_type", "mult": float|None, ...}}
    """
    # Get target's types
    defender_types_query = """
        MATCH (t:Pokemon {id:$target_id})-[h:HAS_TYPE]->(ty:Type)
        RETURN ty.name
    """
    result = query(defender_types_query, {"target_id": target_id})
    
    if len(result) == 0:
        raise ValueError(f"Pokemon not found: {target_id}")
    
    defender_type_names = [row[0] for row in result]
    
    # Get the move details
    moves_data = {}
    
    for move_id in move_list:
        move_query = """
            MATCH (m:Move {id:$move_id})-[t_rel:IS_TYPE]->(ty:Type)
            RETURN m.name, ty.name AS type, m.category, m.base_power, m.accuracy
        """
        result = query(move_query, {"move_id": move_id})
        
        if len(result) == 0:
            # Move not found
            moves_data[move_id] = {
                "move_type": None,
                "mult": None,
                "error": "move not found"
            }
        else:
            name, type_name, category, base_power, accuracy = result[0]
            
            # Check if it's a status move (category 'status')
            if category.lower() == "status":
                moves_data[move_id] = {
                    "move_type": type_name,
                    "mult": None,
                    "status_move": True
                }
            elif base_power is None or accuracy is None:
                # Unknown move (missing data)
                moves_data[move_id] = {
                    "move_type": type_name,
                    "mult": None,
                    "error": "move not found"
                }
            else:
                # Calculate effectiveness multiplier against target types
                mult = 1.0
                
                for defender_type in defender_type_names:
                    matchup_query = """
                        MATCH (a:Type {name:$atk_type})-[e:EFFECTIVE_VS]->(d:Type {name:$defender_type})
                        RETURN e.multiplier
                    """
                    result = query(matchup_query, {"atk_type": type_name, "defender_type": defender_type})
                    
                    if len(result) > 0:
                        mult *= result[0][0]
                    # else: no edge means neutral (1.0), do nothing
                
                moves_data[move_id] = {
                    "move_type": type_name,
                    "mult": float(mult),
                    "status_move": False
                }
    
    # Find best multiplier among damaging moves (non-status, no error)
    best_mult = None
    best_moves = []
    
    for move_id, data in moves_data.items():
        if "error" in data:
            continue
        
        # Skip status moves (they have mult=None anyway but explicitly check)
        if data.get("status_move") is True:
            continue
        
        if data["mult"] is not None:
            if best_mult is None or data["mult"] > best_mult:
                best_mult = data["mult"]
                best_moves = [move_id]
            elif data["mult"] == best_mult and move_id not in best_moves:
                best_moves.append(move_id)
    
    return {
        "best_mult": best_mult,
        "best_moves": best_moves,
        "by_move": moves_data
    }
