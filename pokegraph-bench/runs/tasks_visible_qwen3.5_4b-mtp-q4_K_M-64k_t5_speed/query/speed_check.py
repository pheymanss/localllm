"""Speed calculation for Pokemon battles (spec section 8)."""
from math import floor
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])
from stats import calc_stat, apply_boost, NATURES

# Import query from kuzu_conn
from kuzu_conn import query


def get_base_speed_from_id(pokemon_id):
    """Get a Pokemon's base speed by querying the graph."""
    # The Pokemon node returns: (id, name, gender, species, form_name, hp_base, atk_base, def_base, spe_base, spa_base, spd_base)
    # Base speed is 9th element (index 8) in zero-based indexing
    res = query(f"MATCH (p:Pokemon {{id:'{pokemon_id}'}}) RETURN p.*")
    if res and len(res) > 0:
        row = res[0][0]  # Row data
        # Extract base stats from the tuple: (id, name, gender, species, form_name, hp_base, atk_base, def_base, spe_base, spa_base, spd_base)
        # spe_base is at index 8
        base = row[8] if row else None
        return base
    return None


def get_base_speed_side(s):
    """Get base speed for a side."""
    pokemon_id = s.get('id')
    base = get_base_speed_from_id(pokemon_id)
    return base


def check_side(s, field):
    """Check speed for one side given current field state."""
    # Each side: {id, level=100, nature, evs, ivs, boosts, item, ability, status}
    # Field: {weather, terrain, tailwind: ["a"|"b", ...], trick_room: bool}

    # Extract values with defaults
    level = s.get('level', 100)
    nature = s.get('nature')
    evs = s.get('evs', {})
    ivs = s.get('ivs', {})
    boosts = s.get('boosts')
    item = s.get('item')
    ability = s.get('ability')
    status = s.get('status')

    # Step 1: Base speed from graph, calc_stat with EV/IV/nature/level, then apply_boost with boosts["spe"]
    base_speed = get_base_speed_side(s)

    ev = evs.get('spe', 0)
    iv = ivs.get('spe', 31)

    # Apply nature modifier from stats.py (already correct formula in calc_stat)
    stat_after_nature = calc_stat(base_speed, ev, iv, level, nature)

    # Step 1 continued: apply boost with boosts["spe"]
    speed = apply_boost(stat_after_nature, boosts.get('spe', 0))

    # Step 2: Item multiplier (choicescarf -> x1.5, ironball/machobrace -> x0.5)
    if item == 'choicescarf':
        speed *= 1.5
    elif item in ('ironball', 'machobrace'):
        speed *= 0.5

    # Step 3: Ability multiplier (weather/terrain based)
    weather = field.get('weather') or s.get('weather')
    terrain = field.get('terrain') or s.get('terrain')

    if ability == 'unburden':
        speed *= 2.0
    elif ability is not None and (weather or terrain):
        # Check if this ability activates based on current weather/terrain
        ab_triggers = {
            'swiftswim': ('rain', 'heavyrain'),
            'chlorophyll': ('sun', 'harshsunlight'),
            'sandrush': ('sand'),
            'slushrush': ('snow'),
            'surgesurfer': ('electric')
        }

        for ab, triggers in ab_triggers.items():
            if ability == ab:
                if terrain is not None and terrain in triggers:
                    speed *= 2.0
                elif weather is not None and weather in triggers:
                    speed *= 2.0

    # Step 4: Paralysis x0.5 for Gen 7+
    if status == 'par':
        speed *= 0.5

    # Step 5: Tailwind multiplier (only if side's key is in field["tailwind"])
    tailwind = field.get('tailwind', [])
    if 'a' in tailwind:
        speed *= 2.0
    elif 'b' in tailwind:
        speed *= 2.0

    speed = floor(speed)
    return speed


def speed_check(a, b, field=None):
    """Calculate the winner of a speed check between two Pokemon sides."""
    if field is None:
        field = {}

    a_speed = check_side(a, field)
    b_speed = check_side(b, field)

    # Trick room inverts comparison but doesn't affect tie
    if 'trick_room' in field and field['trick_room']:
        if a_speed > b_speed:
            winner = 'b'
        elif b_speed > a_speed:
            winner = 'a'
        else:
            winner = 'tie'
    else:
        if a_speed > b_speed:
            winner = 'a'
        elif b_speed > a_speed:
            winner = 'b'
        else:
            winner = 'tie'

    return {
        'winner': winner,
        'a_speed': a_speed,
        'b_speed': b_speed,
        'tied': (a_speed == b_speed)
    }


if __name__ == '__main__':
    # Test with the scarf case
    a = {'id': 'garchomp', 'nature': 'jolly', 'evs': {'spe': 252}}
    b = {'id': 'garchomp', 'nature': 'jolly', 'evs': {'spe': 252}, 'item': 'choicescarf'}

    result = speed_check(a, b, None)
    print(f"Scarf test: a_speed={result['a_speed']}, b_speed={result['b_speed']}, winner={result['winner']}")
    print(f"Expected: a_speed=333, b_speed=499, winner=b")
