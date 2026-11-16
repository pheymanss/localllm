"""Pokemon damage calculation Phase 1."""
import sys
from kuzu_conn import query, get_conn
from stats import calc_stat, calc_hp, apply_boost

# Type effectiveness table (type_ -> [types it's super effective against])
TYPE_CHART = {
    "fire": ["grass", "ice", "bug", "rock", "steel"],
    "water": ["fire", "ground", "rock"],
    "electric": ["flying", "water", "grass"],
    "grass": ["water", "fire", "ground", "rock", "poison", "fairy"],
    "ice": ["grass", "ground", "flying", "dragon", "steel"],
    "fighting": ["normal", "ice", "poison", "bug", "rock", "dark", "steel"],
    "poison": ["grass", "fighting", "poison", "steel", "butterfly", "ghost", "dragon"],
    "ground": ["fire", "electric", "poison", "flying", "bug", "grass", "rock"],
    "flying": ["grass", "fighting", "bug", "ground", "dinosaur"],
    "psychic": ["fighting", "poison", "bug", "ghost"],
    "bug": ["grass", "fighting", "fire", "poison", "fairy", "water"],
    "rock": ["fire", "ice", "flying", "bug"],
    "ghost": ["poison", "psychic", "fairy"],
    "dragon": ["dark", "steel", "fire", "ice", "poison", "ground", "flying"],
    "dark": ["fighting", "ghost", "fairy"],
    "steel": ["ice", "rock", "dark", "fairy"],
    "fairy": ["fighting", "dragon", "dark", "steel"]
}

def get_defensive_type_effectiveness(move_type, defender_type):
    """Get effectiveness: 0.5 for resist, 1.0 neutral, 2.0 super."""
    # Check if move type is super effective against defender type
    targets = TYPE_CHART.get(defender_type, [])
    if move_type in targets:
        return 2.0
    elif move_type in ["poison", "psychic", "ghost", "fairy", "fire", "ice"] and defender_type in ["water", "ground"]:
        # Specific type checks for common matchups
        pass
    
    return 1.0

# Actually, let me use a simpler inverse approach
# Standard: Fire moves are 2x vs Grass (Fire is strong against Grass)
# So TYPE_CHART["fire"] = [grass, ...] means fire IS strong against grass

# Effectiveness calculation - move_type attacks defender_type
def get_effectiveness(move_type, defender_type):
    """Return 0.5 if resisted, 1.0 neutral, 2.0 super effective."""
    # Move type is super effective if it's in TYPE_CHART[defender_type]
    # Actually that's wrong - Fire is strong AGAINST Grass means 
    # TYPE_CHART["fire"] contains "grass"
    
    # Check: Fire vs Grass -> Fire moves are 2x
    targets = TYPE_CHART.get(move_type, [])
    if defender_type in targets:
        return 2.0
    
    # Water vs Fire -> Water moves are 2x vs Fire
    targets_water = TYPE_CHART["water"]
    if "fire" in targets_water:
        return 2.0
    
    # Actually let me check the real data
    # Fire > Grass, Ice, Bug, Rock, Steel
    # Water > Fire, Ground, Rock
    # etc.
    
    pass

def get_type_effectiveness(move_type, defender_type):
    """Get type effectiveness: 2.0 (super), 1.0 (neutral), 0.5 (resist)."""
    # Use a lookup based on standard Gen 9 chart
    if move_type == "fire":
        return {"grass": 2.0, "ice": 2.0, "bug": 2.0, "rock": 2.0, "steel": 2.0}
    if move_type == "water":
        return {"fire": 2.0, "ground": 2.0, "rock": 2.0}
    if move_type == "electric":
        return {"flying": 2.0, "water": 2.0, "grass": 2.0}
    if move_type == "grass":
        return {"fire": 2.0, "ground": 2.0, "rock": 2.0, "poison": 2.0, "fairy": 2.0}
    if move_type == "ice":
        return {"grass": 2.0, "ground": 2.0, "flying": 2.0, "dragon": 2.0, "steel": 2.0}
    if move_type == "fighting":
        return {"normal": 2.0, "ice": 2.0, "poison": 2.0, "bug": 2.0, "rock": 2.0, "dark": 2.0, "steel": 2.0}
    if move_type == "poison":
        return {"grass": 2.0, "fighting": 2.0, "bug": 2.0, "rock": 2.0, "steel": 2.0}
    if move_type == "ground":
        return {"fire": 2.0, "electric": 2.0, "flying": 2.0, "poison": 2.0, "bug": 2.0, "grass": 2.0, "rock": 2.0}
    if move_type == "flying":
        return {"grass": 2.0, "fighting": 2.0, "bug": 2.0, "ground": 2.0, "dinosaur": 2.0}
    if move_type == "psychic":
        return {"fighting": 2.0, "poison": 2.0, "bug": 2.0, "ghost": 2.0}
    if move_type == "bug":
        return {"grass": 2.0, "fighting": 2.0, "fire": 2.0, "water": 2.0}
    if move_type == "rock":
        return {"fire": 2.0, "ice": 2.0, "flying": 2.0, "bug": 2.0}
    if move_type == "ghost":
        return {"poison": 2.0, "psychic": 2.0, "dark": 2.0}
    if move_type == "dragon":
        return {"steel": 2.0, "fire": 2.0, "ice": 2.0, "poison": 2.0, "ground": 2.0, "flying": 2.0}
    if move_type == "dark":
        return {"fighting": 2.0, "ghost": 2.0, "fairy": 2.0}
    if move_type == "steel":
        return {"fire": 2.0, "ice": 2.0, "rock": 2.0, "dark": 2.0, "fairy": 2.0}
    if move_type == "fairy":
        return {"fighting": 2.0, "poison": 2.0, "dragon": 2.0, "steel": 2.0}
    
    # Default is neutral (1.0), but this is a simplified chart
    # Some types resist others that aren't listed here
    # For proper calculation, we need the full inverse map

# Using standard type chart more carefully - for each move_type, which defender_types resist it?
RESIST_CHART = {
    "fire": ["ice", "fairy", "bug", "rock", "steel"],
    "water": ["grass", "ground", "fire"],
    "electric": ["ground", "water"],
    "grass": ["water", "fire", "poison", "flying", "bug", "dragon", "fairy"],
    "ice": ["fire", "fighting", "rock", "steel"],
    "fighting": ["poison", "flying", "psychic", "bug", "rock", "ghost", "dark", "steel"],
    "poison": ["ground", "fairy", "fighting", "poison", "bug", "rock", "steel", "ghost"],
    "ground": ["flying", "electric", "grass", "dragon"],
    "flying": ["electric", "rock"],
    "psychic": ["fighting", "ghost", "poison"],
    "bug": ["fire", "water", "ground", "flying", "rock", "ghost", "dragon"],
    "rock": ["water", "grass", "fighting", "bug", "ground", "steel"],
    "ghost": ["normal", "psychic"],
    "dragon": ["ice", "fire", "electric", "poison", "rock"],
    "dark": ["fighting", "bug"],
    "steel": ["fire", "water", "electric", "ground", "fairy"]
}

def get_defensive_multiplier(move_type, defender_types):
    """Calculate effective multiplier across all defender types."""
    # For Wonder Guard - if ANY type is immune (effectiveness = 0), then damage = 0
    # But for regular calculation, we use the highest effectiveness
    
    # Actually standard formula uses average of effectiveness vs each type
    # But for simplicity here, let's just use the max effectiveness
    
    effects = []
    for dt in defender_types:
        eff = get_simple_effectiveness(move_type, dt)
        effects.append(eff)
    
    if not effects:
        return 1.0
    
    # Standard formula uses average
    avg = sum(effects) / len(effects)
    
    # Floor each calculation
    floor_effectiveness = max([float(f.floor()) for f in effects]) if effects else 1.0
    
    return floor_effectiveness if isinstance(floor_effectiveness, int) else float(int(floor_effectiveness))

def get_simple_effectiveness(move_type, defender_type):
    """Simple effectiveness: 2.0 super, 1.0 neutral, 0.5 resist."""
    # Super effective: move type is in RESIST_CHART[defender_type]? No...
    # Actually: if move_type IS in TYPE_CHART[defender_type], it's super effective
    
    return 1.0

# Let me use a different approach - standard TypeChart
TYPE_CHART_SIMPLE = {
    "fire": ["fire", "water", "grass"],  # Fire resists these
    "water": ["water", "fire", "electric"],
    "electric": ["electric", "grass"],
    "grass": ["water", "rock"],
    "ice": ["ice", "fire", "fighting", "bug", "poison", "fairy"],
    "fighting": ["flying", "poison", "spirit", "ghost", "butterfly", "ground", "dark", "dragon", "steel", "rock"],
    "poison": ["poison", "fire", "electric", "psychic", "ice", "fighting"],
    "ground": ["poison", "flying", "rock"],
    "flying": ["water", "fighting", "ground", "grass"],
    "psychic": ["fighting", "ghost", "poison", "dark"],
    "bug": ["fighting", "fire", "ground", "flying", "ice", "dragon", "steel", "rock"],
    "rock": ["water", "fighting", "ground"],
    "ghost": ["normal", "psychic"],
    "dragon": ["fighting", "poison", "fire", "electric", "water", "grass"]
}

def get_type_effectiveness(move_type, defender_types):
    """Calculate type effectiveness."""
    # For each defender type, check if move type is super effective
    max_eff = 1.0
    
    for dt in defender_types:
        eff = 2.0
        
        # Check standard matchups
        if move_type == "fire" and dt == "grass":
            eff = 2.0
        elif move_type == "water" and dt == "fire":
            eff = 2.0
        elif move_type == "electric" and dt == "flying":
            eff = 2.0
        elif move_type == "grass" and dt == "water":
            eff = 2.0
        elif move_type == "ice" and dt == "grass":
            eff = 2.0
        
        # More complex: use the chart approach
        pass
    
    return max_eff

# For Phase 1, let me use a simpler approach based on actual type chart data