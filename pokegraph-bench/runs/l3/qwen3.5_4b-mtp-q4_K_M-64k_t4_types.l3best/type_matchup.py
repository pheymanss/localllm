"""Type matchup calculation (spec section 6)."""
from kuzu_conn import query


def type_matchup(atk_type, defender_id):
    """Calculate the effectiveness of atk_type against defender_id.
    
    Args:
        atk_type: The attacker's type (lowercase string).
        defender_id: The defender's Pokemon id.
        
    Returns:
        float: The total effectiveness multiplier.
        
    Raises:
        ValueError: If the defender is not found or has no types.
    """
    # Get defender's types using the correct defender_id parameter
    result = query(
        "MATCH (p:Pokemon {id:$defender_id})-[h:HAS_TYPE]->(t:Type) RETURN t.name",
        {"defender_id": defender_id}
    )
    
    if len(result) == 0:
        raise ValueError(f"Pokemon not found: {defender_id}")
    
    # Get the types (should be a list of lists, e.g., [['fire'], ['steel']])
    defender_types = result[0]
    
    # Start with 1.0 multiplier
    total_mult = 1.0
    
    for t in defender_types:
        if len(t) == 0:
            continue
        defender_type = t[0]
        
        # Query the EFFECTIVE_VS multiplier from atk_type to defender_type
        mult_result = query(
            "MATCH (a:Type)-[e:EFFECTIVE_VS]->(b:Type) WHERE a.name=$atk AND b.name=$def RETURN e.multiplier",
            {"atk": atk_type, "def": defender_type}
        )
        
        if len(mult_result) > 0:
            total_mult *= mult_result[0][0]
    
    return total_mult
