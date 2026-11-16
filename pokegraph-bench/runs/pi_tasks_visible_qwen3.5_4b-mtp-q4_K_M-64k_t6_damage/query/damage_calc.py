"""Pokemon damage calculation Phase 1."""
from kuzu_conn import query, get_conn
from stats import calc_stat, calc_hp, apply_boost

TYPE_CHART = {
    "fire": {"grass": 2.0, "ice": 2.0, "bug": 2.0, "rock": 2.0, "steel": 2.0},
    "water": {"fire": 2.0, "ground": 2.0, "rock": 2.0},
    "electric": {"flying": 2.0, "water": 2.0, "grass": 2.0},
    "grass": {"water": 2.0, "fire": 2.0, "ground": 2.0, "rock": 2.0, "poison": 2.0, "fairy": 2.0},
    "ice": {"grass": 2.0, "ground": 2.0, "flying": 2.0, "dragon": 2.0, "steel": 2.0},
    "fighting": {"normal": 2.0, "ice": 2.0, "poison": 2.0, "bug": 2.0, "rock": 2.0, "dark": 2.0, "steel": 2.0},
    "poison": {"grass": 2.0, "fighting": 2.0, "poison": 2.0, "bug": 2.0, "rock": 2.0, "ghost": 2.0, "dragon": 2.0},
    "ground": {"fire": 2.0, "electric": 2.0, "poison": 2.0, "flying": 2.0, "bug": 2.0, "grass": 2.0, "rock": 2.0},
    "flying": {"grass": 2.0, "fighting": 2.0, "bug": 2.0, "ground": 2.0},
    "psychic": {"fighting": 2.0, "poison": 2.0, "bug": 2.0, "ghost": 2.0},
    "bug": {"grass": 2.0, "fighting": 2.0, "fire": 2.0, "poison": 2.0, "fairy": 2.0, "water": 2.0},
    "rock": {"fire": 2.0, "ice": 2.0, "flying": 2.0, "bug": 2.0},
    "ghost": {"poison": 2.0, "psychic": 2.0, "dark": 2.0},
    "dragon": {"steel": 2.0, "fire": 2.0, "ice": 2.0, "poison": 2.0, "ground": 2.0, "flying": 2.0},
    "dark": {"fighting": 2.0, "ghost": 2.0, "fairy": 2.0},
    "steel": {"ice": 2.0, "rock": 2.0, "dark": 2.0, "fairy": 2.0},
    "fairy": {"fighting": 2.0, "poison": 2.0, "dragon": 2.0, "steel": 2.0},
}

def get_type_effectiveness(move_type, defender_types):
    """Calculate max type effectiveness multiplier."""
    if not move_type:
        return 1.0
    
    max_eff = 1.0
    for dt in defender_types:
        eff = TYPE_CHART.get(move_type, {}).get(dt.lower(), 1.0)
        if eff == 0 or (isinstance(eff, int) and eff == 0):
            return 0.0
        max_eff = max(max_eff, eff)
    return max_eff

def is_type_immune(move_type, defender_types):
    """Check if any defender type is immune to move type."""
    for dt in defender_types:
        if TYPE_CHART.get(move_type, {}).get(dt.lower(), 1.0) < 1.0:
            return True
    return False

def get_move_data(move_id, conn=None):
    """Get move data from graph."""
    if conn is None:
        conn = get_conn("gen9ou")
    
    res = query("""MATCH (m:Move {id: $id}) RETURN m.base_power as bp, m.category as cat, m.type as tp ORDER BY m.id""", {"id": move_id.lower()})
    
    if not res or len(res) == 0:
        return None
    
    row = res[0]
    bp = row[0]
    cat = row[1]
    tp = row[2]
    
    try:
        bp = int(bp)
    except (ValueError, TypeError):
        bp = 0
    
    def to_str(v):
        if v is None:
            return ""
        try:
            s = str(v).lower()
            return s if len(s) > 0 else ""
        except:
            return ""
    
    return {
        "base_power": bp,
        "category": to_str(cat),
        "type": to_str(tp),
    }

def get_all_stats(conn, pokemon_id):
    """Get all Pokemon stats from graph."""
    res = query("""MATCH (p:Pokemon {id: $id})-[s:HAS_STAT]->(stat:Stat) RETURN s.stat.name as name, floor(s.value) as val ORDER BY s.slot""", {"id": pokemon_id.lower()})
    
    stats = {}
    for row in res:
        try:
            name = str(row[0]).lower()
            value = int(row[1]) if row[1] is not None else 0
            stats[name] = value
        except (ValueError, TypeError):
            pass
    
    return stats

def get_type_list(conn, pokemon_id):
    """Get all Pokemon types from graph."""
    res = query("""MATCH (p:Pokemon {id: $id})-[h:HAS_TYPE]->(t:Type) RETURN t.name ORDER BY h.slot""", {"id": pokemon_id.lower()})
    
    types = []
    for row in res:
        try:
            v = row[0]
            if v is not None:
                types.append(str(v).lower())
        except:
            pass
    
    return types

def get_stat(conn, pokemon_id, stat_name):
    """Get a specific stat value from graph."""
    res = query("""MATCH (p:Pokemon {id: $id})-[s:HAS_STAT]->(stat:Stat) WHERE s.stat.name = $name RETURN floor(s.value) as val""", {"id": pokemon_id.lower(), "name": stat_name.lower()})
    
    if not res or len(res) == 0 or res[0][1] is None:
        return 50
    
    try:
        return int(res[0][1])
    except (ValueError, TypeError):
        return 50

def calc_with_ev(base, ev=0, iv=31, nature=None, stat_name=None):
    """Calculate stat with EV/IV/Nature."""
    if ev is None:
        ev = 0
    if iv is None:
        iv = 31
    
    return calc_stat(base, ev, iv, 100, nature, stat_name)

def damage_calc(attacker, move_id, defender, field=None, crit=False, base_power_override=None):
    """Calculate Pokemon damage."""
    
    conn = get_conn("gen9ou")
    
    # Step 1: Get move data
    move_data = get_move_data(move_id, conn)
    
    if not move_data:
        return (0, 0)
    
    move_category = move_data["category"]
    move_type = move_data["type"]
    base_power = int(move_data["base_power"])
    
    # Step 2a: Status moves return (0, 0)
    if move_category and move_category.lower() == "status":
        return (0, 0)
    
    attacker_id = attacker.get("id", "").lower()
    defender_id = defender.get("id", "").lower()
    level = int(attacker.get("level", 100) or 100)
    
    teratype = attacker.get("tera_type") or None
    
    # Step 3: Psychic Terrain check
    psychic_terrain = field.get("terrain") == "psychic" if field else False
    
    # Terablast: use Tera type as move type if Terastallized
    is_terastallized = teratype and (move_type and move_type.lower() == teratype.lower())
    actual_move_type = move_type if not is_terastallized else (teratype.lower() if teratype else None)
    
    # Step 4: Stat selection - physical vs special
    def select_attacking_stat(move_cat, tera_type):
        if not move_cat:
            return "atk"
        
        cat_lower = move_cat.lower()
        
        # Terablast: physical if Atk >= SpA (after natural stats)
        if actual_move_type and is_terastallized:
            atk_base = get_stat(conn, attacker_id, "attack") or 50
            sp_a_base = get_stat(conn, attacker_id, "special-attack") or 30
            
            atk_val = calc_with_ev(atk_base, 0, 31, None, "atk")
            sp_a_val = calc_with_ev(sp_a_base, 0, 31, None, "spa")
            
            if atk_val >= sp_a_val:
                return "atk"
            else:
                return "spd"
        
        # Foul Play always uses physical/attack stat
        if cat_lower == "physical":
            return "atk"
        
        return cat_lower
    
    def select_defending_stat(move_cat, attacking_stat):
        if not move_cat:
            return None
        
        cat_lower = move_cat.lower()
        
        # Psyshock/Psystrike use defender's SpD
        if move_id.lower() in ["psyshock", "psystrike", "secret sword"] and attacking_stat != "atk":
            return "spd"
        
        # Standard: physical -> Def, special -> SpD
        return "def" if cat_lower == "physical" else "spd"
    
    attacker_stat = select_attacking_stat(move_category, teratype)
    defender_stat = select_defending_stat(move_category, attacker_stat)
    
    # Step 6b: Get stat values with EVs/IVs/Nature
    atk_base = get_stat(conn, attacker_id, "attack") or 50
    sp_a_base = get_stat(conn, attacker_id, "special-attack") or 30
    def_base = get_stat(conn, attacker_id, "defense") or 40
    sp_d_base = get_stat(conn, attacker_id, "special-defense") or 25
    
    nature = attacker.get("nature", "neutral").lower()
    atk_ev = attacker.get("evs", {}).get("atk", 0) or 0
    sp_a_ev = attacker.get("evs", {}).get("spa", 0) or 0
    def_ev = attacker.get("evs", {}).get("def", 0) or 0
    
    atk_val = calc_with_ev(atk_base, atk_ev, 31, nature, "atk")
    sp_a_val = calc_with_ev(sp_a_base, sp_a_ev, 31, None, "spa")
    def_val = calc_with_ev(def_base, def_ev, 31, None, "def")
    
    # Get defender's stats from graph (for normal calculations)
    def_atk_base = get_stat(conn, defender_id, "attack") or 50
    sp_a_def_base = get_stat(conn, defender_id, "special-attack") or 30
    def_def_base = get_stat(conn, defender_id, "defense") or 40
    sp_d_def_base = get_stat(conn, defender_id, "special-defense") or 25
    
    # Apply EVs/IVs to stats (Phase 1: read from input dict for attacker)
    defender_ev = {k: v or 0 for k, v in (defender.get("evs") or {}).items()}
    defender_iv = {k: v or 31 for k, v in (defender.get("ivs") or {}).items()}
    
    atk_def_final = calc_with_ev(def_atk_base, defender_ev.get("atk", 0), defender_iv.get("atk", 31), None, "atk")
    sp_a_def_val = calc_with_ev(sp_a_def_base, defender_ev.get("spa", 0), defender_iv.get("spa", 31), None, "spa")
    def_final = calc_with_ev(def_def_base, defender_ev.get("def", 0), defender_iv.get("def", 31), None, "def")
    sp_d_def_val = calc_with_ev(sp_d_def_base, defender_ev.get("spd", 0), defender_iv.get("spd", 31), None, "spd")
    
    # Step 9: Check for zero base power
    bp = base_power or (base_power_override if base_power_override is not None else 0)
    
    if bp <= 0 and base_power_override is None:
        raise ValueError("Invalid base power, use base_power_override")
    
    # Step 10a: Weather multiplier
    field_weather = field.get("weather") if field else None
    
    def apply_weather_mult(damage, move_type):
        if not damage or damage <= 0:
            return damage
        
        special_cases = {("harshsunlight", "water"), ("heavyrain", "fire")}
        
        # Special nullification rules
        if (field_weather, move_type.lower()) in special_cases:
            return 0.0
        
        mult_map = {
            "sun": {"fire": 1.5, "water": 0.5},
            "rain": {"water": 1.5, "fire": 0.5},
        }
        
        mult = mult_map.get(field_weather, {}).get(move_type.lower(), 1.0)
        
        # Apply multiplier but floor at end
        return damage * mult
    
    base_damage_raw = ((2 * level / 5 + 2) * bp * atk_val / def_final / 50) + 2
    
    if field_weather and base_damage_raw > 0:
        eff = apply_weather_mult(base_damage_raw, actual_move_type)
    else:
        eff = base_damage_raw
    
    # Step 12: Spread modifier (floor per roll)
    is_spread = field and field.get("is_spread", False)
    
    if is_spread:
        base_spread = int(eff * 0.75)
        rolls = [int(base_spread * r / 100) for r in range(85, 101)]
    else:
        # Calculate full damage without spread first  
        if field_weather and eff > 0:
            mult_map = {
                "sun": {"fire": 1.5, "water": 0.5},
                "rain": {"water": 1.5, "fire": 0.5},
            }
            mult = mult_map.get(field_weather, {}).get(actual_move_type.lower(), 1.0)
            if (field_weather, actual_move_type.lower()) in [("harshsunlight", "water"), ("heavyrain", "fire")]:
                eff = 0
            else:
                eff = base_damage_raw * mult
        
        rolls = [int(eff * r / 100) for r in range(85, 101)]
    
    # Step 14a: Critical hit multiplier
    if crit:
        rolls = [int(roll * 1.5) for roll in rolls]
    
    # Step 17a: Type effectiveness (floor per defender type sequentially)
    def get_effective_type(move_type, defender_types):
        if not move_type:
            return 1.0
        
        max_eff = 1.0
        
        # Check for immunity first
        for dt in defender_types:
            eff = TYPE_CHART.get(move_type, {}).get(dt.lower(), 1.0)
            if eff == 0 or (isinstance(eff, int) and eff == 0):
                return 0.0
        
        # Get max effectiveness
        for dt in defender_types:
            eff = TYPE_CHART.get(move_type, {}).get(dt.lower(), 1.0)
            max_eff = max(max_eff, eff)
        
        return max_eff
    
    type_mult = get_effective_type(actual_move_type, defender_types)
    
    # Apply effectiveness to rolls (floor per roll for simplicity in Phase 1)
    if type_mult != 1.0:
        rolls = [int(roll * type_mult) for roll in rolls]
    
    # Check for Wonder Guard immunity
    if is_type_immune(actual_move_type, defender_types):
        return (0, 0)
    
    # Step 19a: Burn reduction (-50% on physical) unless Guts/Foul Play
    is_burning = attacker.get("status", "").lower() == "brn"
    
    if is_burning and actual_move_type and move_category and not ("guts" in str(attacker_boosts.get("atk", [])) or "foulplay" == move_id.lower()):
        rolls = [int(roll * 0.5) for roll in rolls]
    
    return (min(rolls), max(rolls))
