"""coverage: compute damage coverage for a list of moves against a target Pokemon."""
import os, sys
sys.path.insert(0, os.path.join(os.getcwd(), "query"))
from query.kuzu_conn import query

def _move_lookup(move_id):
    """Look up a move's type and category.

    Returns tuple (type, category) or None if move not found.
    """
    # Get both type and category in separate queries to handle Kuzu's behavior
    type_query = f'MATCH (m:Move {{id:"{move_id}"}}) RETURN m.type'
    type_result = query(type_query, {})

    if not type_result:
        return None  # Will be handled by caller to indicate error

    move_type = type_result[0][0]

    cat_query = f'MATCH (m:Move {{id:"{move_id}"}}) RETURN m.category'
    cat_result = query(cat_query, {})

    if not cat_result:
        return None  # Move exists but has no category - should be status move
    move_category = cat_result[0][0]

    return (move_type, move_category)

def _compute_multiplier(multiplier_type, defender_types):
    """Compute damage multiplier for one type vs a list of defender types.

    Returns None if no EFFECTIVE_VS edge exists (neutral matchup = 1.0).
    """
    # Find first effective VS match
    first_mult_query = f'MATCH (a:Type {{name:"{multiplier_type}"}})-[e:EFFECTIVE_VS]->(d:Type {{name:"{defender_types[0]}"}}) RETURN e.multiplier'
    mult_results = query(first_mult_query, {})

    if not mult_results:
        # No EFFECTIVE_VS edge means neutral (1.0) for the first type
        return 1.0

    mult = float(mult_results[0][0])

    # If there are multiple defender types, we need to multiply through all of them
    for defender_type in defender_types[1:]:
        more_query = f'MATCH (a:Type {{name:"{multiplier_type}"}})-[e:EFFECTIVE_VS]->(d:Type {{name:"{defender_type}"}}) RETURN e.multiplier'
        more_results = query(more_query, {})

        if more_results:
            mult *= float(more_results[0][0])
        else:
            # No edge for this defender type means 1.0 (neutral)
            continue

    return mult

def coverage(move_list, target_id):
    """Compute damage coverage for a list of moves against a target.

    Args:
        move_list: List of move IDs (e.g., ["earthquake", "stoneedge"])
        target_id: The target Pokemon's ID

    Returns:
        dict with keys:
            - best_mult: float or None (highest damage multiplier, None if no damaging moves)
            - best_moves: list of move IDs with the highest multiplier
            - by_move: dict {move_id: {"mult": float|None, "status_move": bool|None}}
    """
    # Get target's types - use inline strings in Cypher
    defender_types_query = f'MATCH (p:Pokemon {{id:"{target_id}"}})-[h:HAS_TYPE]->(t:Type) RETURN t.name'
    defender_results = query(defender_types_query, {})

    if not defender_results:
        raise ValueError(f"Pokemon not found: {target_id}")

    types = sorted(set(t[0] for t in defender_results))

    # Initialize by_move dict
    by_move = {}

    # Track best multiplier and moves
    best_mult = None  # Will be updated with damaging moves
    best_moves = []

    # Process each move
    for move_id in move_list:
        # Look up the move's type and category
        type_data = _move_lookup(move_id)

        if type_data is None:
            # Move not found - store error marker
            by_move[move_id] = {"mult": None, "error": "move not found"}
            continue

        move_type, move_category = type_data

        # Check if it's a status move (special category)
        is_status_move = (move_category == "status")

        if is_status_move:
            by_move[move_id] = {"move_type": move_type, "mult": None, "status_move": True}
            continue

        # Compute damage multiplier for this move type against target
        mult = _compute_multiplier(move_type, types)

        by_move[move_id] = {"move_type": move_type, "mult": mult}

        # Track best moves (only consider damaging moves with actual multipliers)
        if mult is not None:
            if best_mult is None or mult > best_mult:
                best_mult = mult
                best_moves = [move_id]
            elif mult == best_mult and move_id not in best_moves:
                best_moves.append(move_id)

    # Build result
    result = {"best_mult": best_mult, "best_moves": sorted(best_moves), "by_move": by_move}

    return result
