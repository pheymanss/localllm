"""Phase 1 damage calc: formula, STAB (incl. Tera), type, burn, screens, weather, crit, spread."""
from math import floor
from kuzu_conn import query
from stats import calc_stat, apply_boost
def _mon(pid):
    r = query("MATCH (p:Pokemon {id:$id}) RETURN p.hp,p.atk,p.def,p.spa,p.spd,p.spe", {"id": pid})
    if not r: raise ValueError(f"Pokemon not found: {pid}")
    types = [x[0] for x in query("MATCH (p:Pokemon {id:$id})-[h:HAS_TYPE]->(t) RETURN t.name ORDER BY h.slot", {"id": pid})]
    return dict(zip(["hp","atk","def","spa","spd","spe"], r[0])), types
def _stat(side, base, name, boost_mode=None):
    s = calc_stat(base[name], (side.get("evs") or {}).get(name, 0), (side.get("ivs") or {}).get(name), side.get("level", 100), side.get("nature"), name)
    b = (side.get("boosts") or {}).get(name, 0)
    return apply_boost(s, b, ignore_negative=boost_mode == "atk", ignore_positive=boost_mode == "def")
def damage_calc(attacker, move_id, defender, field=None, crit=False, base_power_override=None):
    field = field or {}
    r = query("MATCH (m:Move {id:$id}) RETURN m.base_power, m.category, m.type", {"id": move_id})
    if not r: raise ValueError(f"Move not found: {move_id}")
    bp, cat, mtype = r[0]
    if cat == "status": return (0, 0)
    if base_power_override is not None: bp = base_power_override
    if not bp: raise ValueError("variable base power: pass base_power_override")
    abase, atypes = _mon(attacker["id"]); dbase, dtypes = _mon(defender["id"])
    atera = (attacker.get("tera_type") or "").lower() or None; dtera = (defender.get("tera_type") or "").lower() or None
    if dtera: dtypes = [dtera]
    a_name, d_name = ("atk", "def") if cat == "physical" else ("spa", "spd")
    A = _stat(attacker, abase, a_name, "atk" if crit else None); D = _stat(defender, dbase, d_name, "def" if crit else None)
    weather = field.get("weather"); w = 1.0
    if weather in ("sun", "harshsunlight"): w = 1.5 if mtype == "fire" else (0.0 if weather == "harshsunlight" else 0.5) if mtype == "water" else 1.0
    if weather in ("rain", "heavyrain"): w = 1.5 if mtype == "water" else (0.0 if weather == "heavyrain" else 0.5) if mtype == "fire" else 1.0
    if w == 0: return (0, 0)
    level = attacker.get("level", 100)
    dmg = floor(floor(2 * level / 5 + 2) * bp * A / D / 50) + 2
    if field.get("is_spread"): dmg = floor(dmg * 0.75)
    dmg = floor(dmg * w)
    if crit: dmg = floor(dmg * 1.5)
    rolls = [floor(dmg * r / 100) for r in range(85, 101)]
    if atera:
        stab = (2.0 if atera in atypes else 1.5) if mtype == atera else 1.0
    else:
        stab = 1.5 if mtype in atypes else 1.0
    rolls = [floor(x * stab) for x in rolls]
    for t in dtypes:
        e = query("MATCH (a:Type {name:$a})-[e:EFFECTIVE_VS]->(d:Type {name:$d}) RETURN e.multiplier", {"a": mtype, "d": t})
        m = e[0][0] if e else 1.0
        if m == 0: return (0, 0)
        rolls = [floor(x * m) for x in rolls]
    if attacker.get("status") == "brn" and cat == "physical": rolls = [floor(x * 0.5) for x in rolls]
    scr = set((field.get("screens") or {}).get("defender", [])); f = 1.0
    if not crit and ("auroraveil" in scr or ("reflect" in scr and cat == "physical") or ("lightscreen" in scr and cat == "special")): f *= 0.5
    if f != 1.0: rolls = [floor(x * f) for x in rolls]
    return (min(rolls), max(rolls))
