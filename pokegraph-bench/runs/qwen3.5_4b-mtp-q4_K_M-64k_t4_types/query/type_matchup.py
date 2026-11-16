"""Compute effective type matchups for Pokemon."""
from query.kuzu_conn import query


def type_matchup(atk_type: str, defender_id: str) -> float:
    """Compute the effective damage multiplier from attacking type vs defender.

    Args:
        atk_type: The attacking type (lowercase string)
        defender_id: The Pokemon ID

    Returns:
        float: Effective damage multiplier

    Raises:
        ValueError: If the defender Pokemon has no types
    """
    # Get defender's types
    result = query(
        "MATCH (p:Pokemon {id:$defender_id})-[h:HAS_TYPE]->(t:Type) RETURN t.name AS type",
        {"defender_id": defender_id}
    )

    if not result:
        raise ValueError(f"Pokemon not found: {defender_id}")

    defender_types = [r["type"] for r in result]

    # Build IN clause - EFFECTIVE_VS goes from (attacker) -> (defender), so we want edges from atk_type to each defender type
    # We multiply by each EFFECTIVE_VS multiplier found (for multi-type defenses)
    types_in_clause = ", ".join([f"'{t}'" for t in defender_types])

    result = query(
        f"""MATCH (atk:Type {{name:'{atk_type}'}})-[:EFFECTIVE_VS]->(m)
        WHERE m.name IN ({types_in_clause})
        RETURN COALESCE(m.multiplier, 1.0) AS multiplier""",
        {}
    )

    multipliers = [r["multiplier"] for r in result] if result else []

    # Start with 1.0 and multiply by each EFFECTIVE_VS multiplier found (for multi-type defenses)
    return float(1.0 * m for m in multipliers)
