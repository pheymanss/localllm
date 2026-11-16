import sys
sys.path.insert(0, 'query')
from kuzu_conn import query

# Check garchomp types
print('Garchomp types:', query('MATCH (p:Pokemon {id:$id})-[h:HAS_TYPE]->(t:Type) RETURN t.name ORDER BY h.slot', {'id': 'garchomp'}))

# Check heatran stats and types
print('Heatran stats:', query('MATCH (p:Pokemon {id:$id}) RETURN p.hp, p.atk, p.def, p.spa, p.spd, p.spe ORDER BY 1', {'id': 'heatran'}))
print('Heatran types:', query('MATCH (p:Pokemon {id:$id})-[h:HAS_TYPE]->(t:Type) RETURN t.name ORDER BY h.slot', {'id': 'heatran'}))

# Check skarmory stats and types  
print('Skarmory stats:', query('MATCH (p:Pokemon {id:$id}) RETURN p.hp, p.atk, p.def, p.spa, p.spd, p.spe ORDER BY 1', {'id': 'skarmory'}))
print('Skarmory types:', query('MATCH (p:Pokemon {id:$id})-[h:HAS_TYPE]->(t:Type) RETURN t.name ORDER BY h.slot', {'id': 'skarmory'}))

# Check rotomwash stats and types
print('Rotomwash stats:', query('MATCH (p:Pokemon {id:$id}) RETURN p.hp, p.atk, p.def, p.spa, p.spd, p.spe ORDER BY 1', {'id': 'rotomwash'}))
print('Rotomwash types:', query('MATCH (p:Pokemon {id:$id})-[h:HAS_TYPE]->(t:Type) RETURN t.name ORDER BY h.slot', {'id': 'rotomwash'}))

# Check moves
moves = ['stoneedge', 'terablast', 'lowkick', 'hydropump', 'fireblast', 'earthquake', 'swordsdance']
for m in moves:
    move = query('MATCH (m:Move {id:$id}) RETURN m.base_power, m.category, m.type ORDER BY 1', {'id': m})
    print(f'{m}: {move}')
