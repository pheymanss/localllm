"""type_matchup: compute damage multiplier for one type vs a Pokemon."""
import os, sys
sys.path.insert(0, os.path.join(os.getcwd(), "query"))
from query.kuzu_conn import query

def type_matchup(atk_type, defender_id):
    """Compute the effective damage multiplier for atk_type vs defender.

    Args:
        atk_type: The attacker's type (e.g., "fire", "ground")
        defender_id: The Pokemon's ID

    Returns:
        float: The total multiplier (1.0 base * product of all EFFECTIVE_VS)

    Raises:
        ValueError: If the defender Pokemon has no types
    """
    # Get the defender's types - use inline strings in Cypher since kuzu_conn doesn't seem to support $param format
    defender_types_query = f'MATCH (p:Pokemon {{id:"{defender_id}"}})-[h:HAS_TYPE]->(t:Type) RETURN t.name'
    defender_results = query(defender_types_query, {})

    if not defender_results:
        raise ValueError(f"Pokemon not found: {defender_id}")

    # Extract the unique types (a Pokemon can have up to 2 types)
    types = sorted(set(t[0] for t in defender_results))

    # Start with base multiplier of 1.0
    multiplier = 1.0

    # For each defender type, look up EFFECTIVE_VS multipliers
    for defender_type in types:
        effective_vs_query = f'MATCH (a:Type {{name:"{atk_type}"}})-[e:EFFECTIVE_VS]->(d:Type {{name:"{defender_type}"}}) RETURN e.multiplier'
        mult_results = query(effective_vs_query, {})

        # If no edge exists, multiplier is 1.0 (neutral)
        if not mult_results:
            continue

        # Get the first (and only) multiplier from EFFECTIVE_VS
        mult = float(mult_results[0][0])
        multiplier *= mult

    return multiplier
