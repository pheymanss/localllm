"""Shared helpers for reading the PokeGraph DB (spec section 4).

Note: parameters bound in a `WHERE` clause do not work in this Kuzu build, so
lookups that filter on a property use a full table scan plus an in-Python dict
instead of an in-Cypher filter.
"""
from kuzu_conn import query

# {attacker_type: {defender_type: multiplier}} for EFFECTIVE_VS edges.
# Absent keys mean 1x, matching the graph convention.
_EDGE_LOOKUP = {}


def edge_lookup():
    """Populate and return the EFFECTIVE_VS multiplier table."""
    if not _EDGE_LOOKUP:
        edges = query("MATCH (a:Type)-[e:EFFECTIVE_VS]->(b:Type) "
                      "RETURN a.name, b.name, e.multiplier")
        _EDGE_LOOKUP.clear()
        for a, b, m in edges:
            _EDGE_LOOKUP.setdefault(a, {})[b] = float(m)
    return _EDGE_LOOKUP