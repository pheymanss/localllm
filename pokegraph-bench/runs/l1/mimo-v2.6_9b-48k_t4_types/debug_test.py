import sys
sys.path.insert(0, 'query')
from kuzu_conn import get_conn, query

conn1 = get_conn()
print('conn1:', conn1)
r2 = query('MATCH (a:Type {name:$a})-[e:EFFECTIVE_VS]->(b:Type {name:$b}) RETURN e.multiplier',
           {'a': 'ground', 'b': 'fire'})
print('r2 via query():', r2)

# Now call get_conn again and run directly on it
conn2 = get_conn()
print('conn2:', conn2, 'same?', conn1 is conn2)
res = conn2.execute('MATCH (a:Type {name:$a})-[e:EFFECTIVE_VS]->(b:Type {name:$b}) RETURN e.multiplier', {'a': 'ground', 'b': 'fire'})
rows = []
while res.has_next(): rows.append(res.get_next())
print('direct execute:', rows)