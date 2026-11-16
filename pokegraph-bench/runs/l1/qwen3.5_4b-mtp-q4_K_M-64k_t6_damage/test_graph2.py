import sys
sys.path.insert(0, 'query')
from kuzu_conn import query

# Move
move = query("MATCH (m:Move {id:'earthquake'}) RETURN m.base_power, m.category, m.type", {})

# Garchomp stats  
garchomp_stats = query("MATCH (p:Pokemon {id:'garchomp'}) RETURN p.hp, p.atk, p.def, p.spa, p.spd, p.spe ORDER BY 1", {})
heatran_stats = query("MATCH (p:Pokemon {id:'heatran'}) RETURN p.hp, p.atk, p.def, p.spa, p.spd, p.spe ORDER BY 1", {})

print("Move Earthquake:", move[0])
print("Garchomp stats:", garchomp_stats[0])
print("Heatran stats:", heatran_stats[0])

g_types = query("MATCH (p:Pokemon {id:'garchomp'})-[h:HAS_TYPE]->(t:Type) RETURN t.name ORDER BY h.slot", {'id':'garchomp'})
d_types = query("MATCH (p:Pokemon {id:'heatran'})-[h:HAS_TYPE]->(t:Type) RETURN t.name ORDER BY h.slot", {'id':'heatran'})

print("Garchomp types:", g_types[0])
print("Heatran types:", d_types[0])
