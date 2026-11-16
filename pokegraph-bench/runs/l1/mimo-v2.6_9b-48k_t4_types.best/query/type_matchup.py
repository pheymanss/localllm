"""Compute how super effective an attacking type is vs a Pokemon's typing."""
from kuzu_conn import query, get_conn

def type_matchup(atk_type, defender_id) -> float:
    conn = get_conn()
    types = query('MATCH (p:Pokemon {id:$id})-[:HAS_TYPE]->(t:Type) RETURN t.name ORDER BY p.id',
                  {"id": defender_id})
    if not types:
        raise ValueError(f"Pokemon not found: {defender_id}")

    mult = 1.0
    for t in types:
        rows = query('MATCH (a:Type {name:$a})-[e:EFFECTIVE_VS]->(b:Type {name:$b}) RETURN e.multiplier',
                     {"a": atk_type, "b": t})
        if rows:
            mult *= rows[0][0]
    return mult