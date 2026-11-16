"""Type effectiveness: attacker type vs a Pokemon's types (spec section 6)."""
from kuzu_conn import query

def target_types(defender_id):
    """Return the list of a Pokemon's type names, ordered by HAS_TYPE slot."""
    rows = query(
        """
        MATCH (p:Pokemon {id:$defender_id})-[h:HAS_TYPE]->(t:Type)
        RETURN t.name AS type, h.slot AS slot
        ORDER BY h.slot, t.name
        """,
        {"defender_id": defender_id},
    )
    if not rows:
        raise ValueError(f"Pokemon not found: {defender_id}")
    return [type_name for type_name, _ in rows]

def type_matchup(atk_type, defender_id):
    """Return the type-matchup multiplier of `atk_type` against Pokemon `defender_id`.

    Starts at 1.0 and multiplies by each EFFECTIVE_VS multiplier the defender
    has (missing edges are 1x, multiplier 0.0 is immunity).
    """
    mult = 1.0
    for tname in target_types(defender_id):
        rows = query(
            """
            MATCH (a:Type)-[e:EFFECTIVE_VS]->(b:Type)
            WHERE a.name = $atk_type AND b.name = $tname
            RETURN e.multiplier AS mult
            """,
            {"atk_type": atk_type, "tname": tname},
        )
        mult *= rows[0][0] if rows else 1.0
    return float(mult)