"""Speed comparison helper (spec section 7)."""
from math import floor

import sys

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kuzu_conn import query  # noqa: E402
from stats import apply_boost, calc_stat  # noqa: E402


def _floor(x):
    return floor(x)


WEATHER_ABILITIES = {
    "swiftswim": "rain",
    "chlorophyll": "sun",
    "sandrush": "sand",
    "slushrush": "snow",
    "surgesurfer": "electric",
}

# aliases for weather elements (e.g. harshsunlight counts as sun)
WEATHER_ALIAS = {
    "sun": ("harshsunlight",),
    "rain": ("heavyrain",),
    "sand": (),
    "snow": (),
    "electric": (),
}


def _weather_active(field, ability):
    """True if the field weather/terrain makes this weather ability active."""
    if not ability:
        return False
    element = WEATHER_ABILITIES.get(ability)
    if element is None:
        return False
    raw = (field or {}).get("weather") or (field or {}).get("terrain")
    if raw is None:
        return False
    val = str(raw).strip().lower()
    return val == element or val in WEATHER_ALIAS.get(element, ())


def _apply_side(side, field):
    """Compute one side's effective Speed following the mandated order."""
    # 1. Base Speed from the graph, then apply the (boosted) stat.
    base = query(
        "MATCH (p:Pokemon {id:$id}) RETURN p.spe", {"id": side["id"]}
    )[0][0]
    stat = apply_boost(
        "spe",
        calc_stat(int(base), ev=side.get("evs", {}).get("spe", 0),
                  iv=side.get("ivs", {}).get("spe", 31),
                  level=side.get("level", 100),
                  nature=side.get("nature"), stat_name="spe"),
    )

    # 2. Item held.
    item = side.get("item")
    if item == "choicescarf":
        stat = _floor(stat * 1.5)
    elif item in ("ironball", "machobrace"):
        stat = _floor(stat * 0.5)

    # 3. Ability.
    ability = side.get("ability")
    if ability == "unburden":
        stat = _floor(stat * 2)
    elif _weather_active(field, ability):
        stat = _floor(stat * 2)

    # 4. Paralysis (Gen 7+ value).
    if side.get("status") == "par":
        stat = _floor(stat * 0.5)

    # 5. Tailwind on this side's slot key.
    if field and field.get("tailwind"):
        keys = [str(k).strip().lower() for k in field["tailwind"]]
        if str(side.get("key", "a")).strip().lower() in keys:
            stat = _floor(stat * 2)

    return int(stat)


def speed_check(a, b, field=None):
    a_speed = _apply_side(a, field or {})
    b_speed = _apply_side(b, field or {})

    if field and field.get("trick_room"):
        winner = "a" if b_speed < a_speed else ("b" if a_speed < b_speed else "tie")
    else:
        winner = "a" if a_speed > b_speed else ("b" if b_speed > a_speed else "tie")

    return {
        "winner": winner,
        "a_speed": a_speed,
        "b_speed": b_speed,
        "tied": a_speed == b_speed,
    }