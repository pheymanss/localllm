"""Speed comparison for two sides (spec section 8)."""
from math import floor

from kuzu_conn import query
from stats import apply_boost, calc_stat

# Item multipliers (each floored independently, applied in step order).
ITEM_MULT = {"choicescarf": 1.5, "ironball": 0.5, "machobrace": 0.5}

# Weather/terrain abilities that double Speed when the field matches.
WEATHER_ABILITIES = {
    "swiftswim": {"rain"},
    "chlorophyll": {"sun"},
    "sandrush": {"sand"},
    "slushrush": {"snow"},
    "harshsunlight": {"sun"},
    "heavyrain": {"rain"},
    "surgesurfer": {"electric"},
}


def _base_speed(side):
    """Step 1a: base Speed from the graph."""
    rows = query("MATCH (p:Pokemon {id:$id}) RETURN p.spe AS spe", {"id": side["id"]})
    return calc_stat(
        rows[0][0],
        ev=side.get("evs"),
        iv=side.get("ivs"),
        level=side.get("level"),
        nature=side.get("nature"),
        stat_name="spe",
    )


def _step1(speed, side):
    """Step 1b: apply_boost with boosts["spe"] (absent key -> no change)."""
    return apply_boost(speed, side.get("boosts", {}).get("spe"))


def _item_mult(side):
    """Step 2: item multiplier (default 1.0)."""
    name = side.get("item")
    if not name:
        return 1.0
    return ITEM_MULT.get(str(name).lower()) or 1.0


def _ability_mult(side, field):
    """Step 3: ability multiplier (unburden / weather abilities)."""
    ability = side.get("ability")
    if not ability:
        return 1.0

    name = str(ability).lower()
    if name == "unburden":
        return 2.0

    weather = field.get("weather") if field else None
    terrain = field.get("terrain") if field else None
    if terrain is not None:
        # Electric terrain is stored as the terrain value.
        if terrain == "electric":
            weather = "electric"
    active = None
    for name_ in (weather, terrain):
        if name_ is None:
            continue
        if name in WEATHER_ABILITIES and WEATHER_ABILITIES[name] == {name_}:
            active = name_
    return 2.0 if active else 1.0


def _paralysis_mult(status):
    """Step 4: paralysis halves Speed (Gen 7+ value)."""
    return 0.5 if status == "par" else 1.0


def _tailwind_mult(side, field):
    """Step 5: Tailwind doubles Speed for the side whose key is in field['tailwind']."""
    if not field or "tailwind" not in field:
        return 1.0
    return 2.0 if side.get("key") in field["tailwind"] else 1.0


def speed_check(a, b, field=None) -> dict:
    """Calculate and compare Pokemon speed for sides 'a' and 'b'.

    Each side: {id, level=100, nature, evs, ivs, boosts, item, ability, status}
    Field: {weather, terrain, tailwind: ["a"|"b", ...], trick_room: bool}

    Computation order per side:
    1. Base Speed from the graph, calc_stat with the side's EV/IV/nature/level, then apply_boost with boosts["spe"]
    2. Item: choicescarf -> floor(x1.5); ironball or machobrace -> floor(x0.5)
    3. Ability (read ONLY from the side dict - no default to slot-0 ability):
       - unburden -> x2 (caller asserts the item was consumed)
       - weather abilities, x2 when active: swiftswim (rain), chlorophyll (sun), sandrush (sand), slushrush (snow), surgesurfer (electric terrain). harshsunlight counts as sun, heavyrain as rain.
    4. Paralysis (status == "par"): floor(x0.5) (Gen 7+ value)
    5. Tailwind: if the side's key ("a"/"b") is in field["tailwind"], floor(x2)

    Each multiplier is floored independently in the order above.

    Returns:
        {"winner": "a"|"b"|"tie", "a_speed": int, "b_speed": int, "tied": bool}
    """
    def calc(side):
        speed = _base_speed(side)
        speed = _step1(speed, side)
        speed = floor(speed * _item_mult(side))
        speed = floor(speed * _ability_mult(side, field))
        speed = floor(speed * _paralysis_mult(side.get("status")))
        speed = floor(speed * _tailwind_mult(side, field))
        return speed

    speed_a = calc(a)
    speed_b = calc(b)

    tied = speed_a == speed_b
    if tied:
        winner = "tie"
    elif field and field.get("trick_room"):
        # Trick Room inverts the comparison (lower speed wins); a tie stays a tie.
        winner = "a" if speed_a < speed_b else "b"
    else:
        winner = "a" if speed_a > speed_b else "b"

    return {"winner": winner, "a_speed": speed_a, "b_speed": speed_b, "tied": tied}