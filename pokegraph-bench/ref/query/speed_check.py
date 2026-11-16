from math import floor
from kuzu_conn import query
from stats import calc_stat, apply_boost
WEATHER_AB = {"swiftswim": {"rain", "heavyrain"}, "chlorophyll": {"sun", "harshsunlight"}, "sandrush": {"sand"}, "slushrush": {"snow"}}
def _speed(side, key, field):
    base = query("MATCH (p:Pokemon {id:$id}) RETURN p.spe", {"id": side["id"]})[0][0]
    s = calc_stat(base, (side.get("evs") or {}).get("spe", 0), (side.get("ivs") or {}).get("spe"), side.get("level", 100), side.get("nature"), "spe")
    s = apply_boost(s, (side.get("boosts") or {}).get("spe", 0))
    item = (side.get("item") or "").lower(); ab = (side.get("ability") or "").lower()
    if item == "choicescarf": s = floor(s * 1.5)
    elif item in ("ironball", "machobrace"): s = floor(s * 0.5)
    if ab == "unburden": s = s * 2
    elif ab in WEATHER_AB and field.get("weather") in WEATHER_AB[ab]: s = s * 2
    elif ab == "surgesurfer" and field.get("terrain") == "electric": s = s * 2
    if side.get("status") == "par": s = floor(s * 0.5)
    if key in (field.get("tailwind") or []): s = s * 2
    return s
def speed_check(a, b, field=None):
    field = field or {}
    sa, sb = _speed(a, "a", field), _speed(b, "b", field)
    if sa == sb: w = "tie"
    elif field.get("trick_room"): w = "a" if sa < sb else "b"
    else: w = "a" if sa > sb else "b"
    return {"winner": w, "a_speed": sa, "b_speed": sb, "tied": sa == sb}
