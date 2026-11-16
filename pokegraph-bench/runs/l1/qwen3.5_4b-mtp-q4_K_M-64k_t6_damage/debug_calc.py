import sys
sys.path.insert(0, 'query')
from stats import calc_stat

# Check what stat the graph has for Garchomp atk  
atk_graph = query("MATCH (p:Pokemon {id:$id}) RETURN p.atk", {"id":"garchomp"})[0][0]
print(f"Garchomp atk from graph: {atk_graph}")

# Base 50 with jolly nature and default iv=31, no evs  
base_atk = 50
result = calc_stat(base_atk, iv=31, level=100, nature="jolly", "atk")
print(f"Base {base_atk} -> {result}")

# With evs=252
result_ev = calc_stat(base_atk, iv=31, level=100, ev=252, nature="jolly", "atk")
print(f"Base {base_atk} with ev=252 -> {result_ev}")
