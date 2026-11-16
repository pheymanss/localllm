"""Type matchup lookup via the Kuzu graph."""
from kuzu_conn import query


def type_matchup(atk_type, defender_id) -> float:
    types = query(
        "MATCH (p:Pokemon {id:$id})-[h:HAS_TYPE]->(t:Type) RETURN t.name", {"id": defender_id}
    )
    if not types:
        raise ValueError(f"Pokemon not found: {defender_id}")
    atk = query(
        "MATCH (t:Type {name:$n})-[h:EFFECTIVE_VS]->(d:Type) RETURN d.name, h.multiplier",
        {"n": atk_type},
    )
    mult = 1.0
    for t in types:
        for d, m in atk:
            if d == t:
                mult *= m
    return mult