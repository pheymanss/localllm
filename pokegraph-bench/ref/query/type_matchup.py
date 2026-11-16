from kuzu_conn import query
def _types(pid):
    return [r[0] for r in query("MATCH (p:Pokemon {id:$id})-[h:HAS_TYPE]->(t:Type) RETURN t.name ORDER BY h.slot", {"id": pid})]
def _mult(atk, types):
    m = 1.0
    for t in types:
        r = query("MATCH (a:Type {name:$a})-[e:EFFECTIVE_VS]->(d:Type {name:$d}) RETURN e.multiplier", {"a": atk, "d": t})
        if r: m *= r[0][0]
    return m
def type_matchup(atk_type, defender_id):
    types = _types(defender_id)
    if not types: raise ValueError(f"Pokemon not found: {defender_id}")
    return _mult(atk_type.lower(), types)
