"""Speed calculation for Pokemon battles (spec section 8)."""
from math import floor
import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])
from kuzu_conn import query
from stats import calc_stat, apply_boost, NATURES

WEATHER_ABILITIES = {"swiftswim": "rain", "chlorophyll": "sun", "sandrush": "sand", "slushrush": "snow", "surgesurfer": "electric"}
HARSH_SUN = "harshsunlight"
HEAVY_RAIN = "heavyrain"

def weather_active(ability, weather):
    """Check if ability is active with given weather."""
    if not ability or not weather:
        return False
    if ability.lower() == HARSH_SUN and weather.lower() == HARSH_SUN:
        return True
    if ability.lower() == HEAVY_RAIN and weather.lower() == HEAVY_RAIN:
        return True
    
    ab_lower = ability.lower()
    wea_lower = weather.lower() if weather else ""
    weather_ability = WEATHER_ABILITIES.get(ab_lower)
    return weather_ability == wea_lower

def get_speed_multiplier(side, field):
    """Calculate speed multiplier for a side."""
    a_id = side.get("id") or ""
    a_level = side.get("level", 100)
    a_nature = (side.get("nature") or "").lower()
    a_evs = side.get("evs") or {}
    a_ivs = side.get("ivs") or {}
    a_boosts = side.get("boosts") or {}
    a_item = side.get("item") or ""
    a_ability = side.get("ability")
    a_status = side.get("status") or ""
    
    # 1. Base Speed from graph, calc_stat with EV/IV/nature/level, then apply_boost with boosts["spe"]
    base_speed = query("MATCH (p:Pokemon {id:$id})-[h:HAS_TYPE]->(t:Type) RETURN h.value AS spe", {"id": a_id})[0][0] if query("MATCH (p:Pokemon {id:$id}) RETURN p.id", {"id": a_id}) else 80
    if base_speed is None:
        raise ValueError(f"Speed for Pokemon '{a_id}' not found")
    
    stat = calc_stat(base_speed, ev=a_evs.get("spe"), iv=a_ivs.get("spe"), level=a_level, nature=a_nature)
    speed = apply_boost(stat, a_boosts.get("spe", 0))
    
    multiplier = speed
    
    # 2. Item modifier
    item = a_item.lower() if a_item else ""
    if item == "choicescarf":
        multiplier = floor(multiplier * 1.5)
    elif item in ("ironball", "machobrace"):
        multiplier = floor(multiplier * 0.5)
    
    # 3. Ability modifier (only if ability is set in the side dict)
    ability = a_ability
    if ability:
        ab_lower = ability.lower()
        weather = field.get("weather") or ""
        terrain = field.get("terrain") or ""
        
        if ab_lower == "unburden":
            multiplier = floor(multiplier * 2.0)
        elif weather and weather_active(ability, weather):
            multiplier = floor(multiplier * 2.0)
    
    # 4. Paralysis modifier (Gen 7+ value: floor(x0.5))
    if a_status == "par":
        multiplier = floor(multiplier * 0.5)
    
    # 5. Tailwind modifier
    field_key = "a" if side.get("id") else "b"
    tailwind = field.get("tailwind", []) or []
    if field_key in tailwind:
        multiplier = floor(multiplier * 2.0)
    
    return int(multiplier)

def speed_check(a, b, field=None):
    """Calculate winner based on speed."""
    field = field or {}
    
    # Get multipliers for both sides
    a_speed = get_speed_multiplier(a, field)
    b_speed = get_speed_multiplier(b, field)
    
    result = {
        "a_speed": a_speed,
        "b_speed": b_speed,
        "tied": False
    }
    
    # Trick room inverts comparison (lower speed wins), but ties stay ties
    if a_speed == b_speed:
        result["winner"] = "tie"
        result["tied"] = True
    elif field.get("trick_room", False):
        if a_speed < b_speed:
            result["winner"] = "b"  # Lower speed wins in trick room
        else:
            result["winner"] = "a"
    else:
        if a_speed > b_speed:
            result["winner"] = "a"
        else:
            result["winner"] = "b"
    
    return result
