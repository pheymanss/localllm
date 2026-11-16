"""type_matchup: Calculate type effectiveness against a defender."""

# Import from sibling module (kuzu_conn is in same directory)
from kuzu_conn import query


def type_matchup(atk_type, defender_id):
    """
    Calculate type effectiveness of atk_type against defender_id.
    
    Args:
        atk_type: The attacker's type (e.g., "ground", "fire")
        defender_id: The defender's Pokemon name
        
    Returns:
        float: Type effectiveness multiplier (1.0 = neutral, 2.0 = super effective, 0.5 = not very effective)
        
    Raises:
        ValueError: If the defender Pokemon is not found
    """
    # Get the defender's types from HAS_TYPE relationship
    defender_types_query = """
        MATCH (d:Pokemon {id:$defender_id})-[h:HAS_TYPE]->(t:Type)
        RETURN t.name
    """
    result = query(defender_types_query, {"defender_id": defender_id})
    
    if len(result) == 0:
        raise ValueError(f"Pokemon not found: {defender_id}")
    
    # Get all type names (lowercase as per schema)
    defender_type_names = [row[0] for row in result]
    
    # Start with 1.0 and multiply by EFFECTIVE_VS multiplier for each defender type
    effectiveness = 1.0
    
    # For each defender type, find the ATTACKER's type -> DEFENDER_TYPE matchup
    for defender_type in defender_type_names:
        matchup_query = """
            MATCH (a:Type {name:$atk_type})-[e:EFFECTIVE_VS]->(d:Type {name:$defender_type})
            RETURN e.multiplier
        """
        result = query(matchup_query, {"atk_type": atk_type, "defender_type": defender_type})
        
        if len(result) > 0:
            # Edge exists, get the multiplier
            effectiveness *= result[0][0]
    
    return effectiveness
