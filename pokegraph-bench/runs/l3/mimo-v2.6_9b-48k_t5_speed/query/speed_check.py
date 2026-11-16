"""Speed comparison logic (spec section 8)."""
from math import floor

from kuzu_conn import query
from stats import apply_boost, calc_stat


def _base_speed(side):
    return calc_stat(query("MATCH (p:Pokemon {id:$id}) RETURN p.spe", {"id": side["id"]})[0][0])


def _item_multiplier(side):
    item = side.get("item")
    if not item:
        return 1.0
    if item == "choicescarf":
        return 1.5
    if item in ("ironball", "machobrace"):
        return 0.5
    return 1.0


def _ability_multiplier(side, speed, field):
    ability = side.get("ability")
    if not ability:
        return 1.0
    mult = 2.0 if ability == "unburden" else 1.0
    weather = field.get("weather") if field else None
    terrain = field.get("terrain") if field else None
    active = False
    if weather == "rain":
        active = ability in ("swiftswim", "heavyrain")
    elif weather == "sun":
        active = ability in ("chlorophyll", "harshsunlight")
    elif weather == "sand":
        active = ability == "sandrush"
    elif weather == "snow":
        active = ability == "slushrush"
    elif terrain == "electric":
        active = ability == "surgesurfer"
    if active:
        mult = 2.0
    return mult


def _speed(side, field):
    speed = apply_boost(_base_speed(side), calc_stat(
        query("MATCH (p:Pokemon {id:$id})-[h:HAS_TYPE]->(t:Type) "
              "RETURN t.name ORDER BY h.slot", {"id": side["id"]})[0][0],
        stat_name="spe")) if False else _base_speed(side)
    speed = apply_boost(speed, side.get("boosts", {}).get("spe", 0))
    speed *= _item_multiplier(side)
    speed *= _ability_multiplier(side, floor(speed), field)
    if side.get("status") == "par":
        speed = floor(speed / 2)
    tw = field.get("tailwind") if field else None
    if tw and side.get("key") in tw:
        speed *= 2.0
    return floor(speed)


def speed_check(a, b, field=None):
    a_speed = _speed(a, field)
    b_speed = _speed(b, field)
    if field and field.get("trick_room"):
        if a_speed == b_speed:
            return {"winner": "tie", "a_speed": a_speed, "b_speed": b_speed, "tied": True}
        return {"winner": "a" if b_speed < a_speed else "b", "a_speed": a_speed,
                "b_speed": b_speed, "tied": False}
    if a_speed == b_speed:
        return {"winner": "tie", "a_speed": a_speed, "b_speed": b_speed, "tied": True}
    return {"winner": "a" if a_speed > b_speed else "b", "a_speed": a_speed,
            "b_speed": b_speed, "tied": False}