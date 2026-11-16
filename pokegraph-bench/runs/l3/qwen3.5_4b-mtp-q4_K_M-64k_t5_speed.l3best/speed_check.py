"""Speed check computation (spec section 8)."""
from math import floor
import sys
sys.path.append("..")  # Make kuzu_conn and stats importable

from kuzu_conn import query, get_conn
from stats import calc_stat, calc_hp, apply_boost

# Weather -> ability mapping
WEATHER_ABILITY = {
    "rain": ["swiftswim"],
    "sun": ["chlorophyll", "harshsunlight"],
    "sand": ["sandrush"],
    "snow": ["slushrush"],
    "electric terrain": ["surgesurfer"],
}

# Terrain -> ability mapping
TERRAIN_ABILITY = {"electric": ["surgesurfer"]}

def get_base_speed(pokemon_id):
    """Get base speed from the graph."""
    res = query("MATCH (p:Pokemon {id:$id}) RETURN p.spe ORDER BY 1 LIMIT 1", {"id": pokemon_id})
    if not res or len(res) == 0:
        return 80  # Default fallback
    base = res[0][0]
    return base

def get_ability(side):
    """Get ability from side dict (no default)."""
    return side.get("ability")

def get_status(side):
    """Get status from side dict."""
    return side.get("status")

def get_ev(side):
    """Get EVs from side dict, returning empty dict if not present."""
    evs = side.get("evs", {})
    return evs if evs else {}

def get_item(side):
    """Get item from side dict."""
    return side.get("item")

def get_nature(side):
    """Get nature from side dict."""
    return side.get("nature")

def get_level(side):
    """Get level from side dict, defaulting to 100."""
    return side.get("level", 100)

def has_weather_active(ability, weather):
    """Check if ability activates based on weather."""
    if not ability or not weather:
        return False
    # Check if the ability is in the list for this weather type
    abilities = WEATHER_ABILITY.get(weather, [])
    return ability in abilities

def get_multiplier(side_dict, is_a, field):
    """Calculate speed multiplier for a side."""
    # 1. Base Speed
    base = get_base_speed(side_dict["id"])
    nature = get_nature(side_dict)
    evs = get_ev(side_dict)
    ivs = side_dict.get("ivs", {})
    level = get_level(side_dict)
    
    speed = calc_stat(base, ev=evs.get("spe", 0), iv=ivs.get("spe", 31), level=level, nature=nature, stat_name="spe")
    
    # Get boosts from the side dict if present
    boosts = side_dict.get("boosts", {})
    
    # Apply boost first (step 1)
    speed = apply_boost(speed, boosts.get("spe", 0))
    
    # 2. Item multiplier (after base speed and boost)
    item = get_item(side_dict)
    if item == "choicescarf":
        speed = floor(speed * 1.5)
    elif item in ("ironball", "machobrace"):
        speed = floor(speed * 0.5)
    
    # 3. Ability multiplier (boosts are applied before ability check per spec order)
    ability = get_ability(side_dict)
    weather = field.get("weather")
    terrain = field.get("terrain")
    
    if has_weather_active(ability, weather):
        speed = floor(speed * 2)
    
    # Check for surgesurfer in electric terrain (step 3 - same as weather ability check)
    if terrain == "electric" and ability == "surgesurfer":
        speed = floor(speed * 2)
    
    # 4. Paralysis multiplier
    status = get_status(side_dict)
    if status == "par":
        speed = floor(speed * 0.5)
    
    # 5. Tailwind multiplier
    tailwind = field.get("tailwind", [])
    if is_a and "a" in tailwind:
        speed = floor(speed * 2)
    elif not is_a and "b" in tailwind:
        speed = floor(speed * 2)
    
    return speed

def speed_check(a, b, field=None):
    """Compute speed comparison between two sides."""
    if field is None:
        field = {}
    
    # Compute speeds for both sides
    a_speed = get_multiplier(a, is_a=True, field=field)
    b_speed = get_multiplier(b, is_a=False, field=field)
    
    # Determine winner
    tied = (a_speed == b_speed)
    
    if tied:
        return {"winner": "tie", "a_speed": a_speed, "b_speed": b_speed, "tied": True}
    
    trick_room = field.get("trick_room", False)
    
    if trick_room:
        # Invert comparison - lower speed wins
        if a_speed < b_speed:
            return {"winner": "a", "a_speed": a_speed, "b_speed": b_speed, "tied": False}
        else:
            return {"winner": "b", "a_speed": a_speed, "b_speed": b_speed, "tied": False}
    else:
        # Normal comparison - higher speed wins
        if a_speed > b_speed:
            return {"winner": "a", "a_speed": a_speed, "b_speed": b_speed, "tied": False}
        else:
            return {"winner": "b", "a_speed": a_speed, "b_speed": b_speed, "tied": False}
