"""Type effectiveness for a Pokemon (spec section 6)."""
from graph_utils import edge_lookup

# A move slot on a Pokemon; the type name is the only thing that matters.
_TYPES_QUERY = ("MATCH (p:Pokemon {id:$id})-[h:HAS_TYPE]->(t:Type) "
                 "RETURN t.name AS type, h.slot AS slot")


def type_matchup(atk_type, defender_id):
    """Attack effectiveness of `atk_type` against `defender_id` (0.0-4.0).

    Starts at 1.0 and multiplies by every EFFECTIVE_VS edge from each of the
    defender's types; an edge that is missing multiplies by 1.0.
    """
    rows = query(_TYPES_QUERY, {"id": defender_id})
    if not rows:
        raise ValueError(f"Pokemon not found: {defender_id}")
    mult = 1.0
    for _, tname in rows:
        mult *= edge_lookup().get(tname, {}).get(atk_type, 1.0)
    return mult