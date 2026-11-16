# Task: Implement `damage_calc` Phase 1

## How to work
- Python: run `python` (3.13; `kuzu`, `json5`, `pytest` installed). Do not pip install anything.
- Run tests with `python -m pytest -q`.
- `query/` is the import root: modules import each other by bare name (e.g. `from kuzu_conn import query`). Tests should add `query/` to `sys.path`.
- Write a few tests of your own in `tests/` and make them pass. Hidden tests will also be run against your code, using exactly the function names and signatures given below.
- Keep your context small: you do NOT need the rest of the spec. Everything you need is in this file.

Create `query/damage_calc.py` with `damage_calc(attacker, move_id, defender, field=None, crit=False, base_power_override=None) -> (min_damage, max_damage)`.

**Phase 1 scope only.** Implement: steps 1, 2 (status, tera types; ignore items and abilities), 4-5 (Tera Blast type, defender Tera), 6 only the plain rule (physical -> Atk vs Def, special -> SpA vs SpD), 7 (incl. crit boost rules), 9 only as "use the move's base_power, `base_power_override` wins, raise ValueError if it resolves to 0", 10-17, 19 (burn), and from step 20 only the screens. Skip items, abilities, variable BP, terrain, helping hand, Parental Bond.
Base stats and types come from the graph (`Pokemon` hp/atk/def/spa/spd/spe, `HAS_TYPE` with `slot`), moves from `Move` (base_power, category, type).

## Provided: `query/kuzu_conn.py`
- `query(cypher, params=None) -> list[list]` runs a read-only Cypher query on `graph/gen9.db` and returns all rows.
  Example: `query("MATCH (p:Pokemon {id:$id})-[h:HAS_TYPE]->(t:Type) RETURN t.name ORDER BY h.slot", {"id": "heatran"})` -> `[["fire"], ["steel"]]`.
- `get_conn()` returns the cached `kuzu.Connection` if you need it directly.

## Provided: `query/stats.py`
`calc_stat(base, ev=0, iv=31, level=100, nature=None, stat_name=None)`, `calc_hp(base, ev=0, iv=31, level=100)`,
`apply_boost(stat, boost, ignore_negative=False, ignore_positive=False)`. `nature` is a lowercase nature name like `"jolly"`. Already correct; use it.

## 9. `damage_calc` - the core

Signature: `damage_calc(attacker: dict, move_id: str, defender: dict, field: dict|None, crit: bool=False, base_power_override: int|None=None) -> (min_damage, max_damage)`.

Returns raw HP damage across the 16 random rolls (85..100). Returns `(0, 0)` for status moves, type immunity, weather-nullified moves (harsh sun vs Water, heavy rain vs Fire), Wonder Guard immunity, and Psychic Terrain blocking priority moves against a grounded defender.

### Input shapes

```
side = {
  "id": "garchomp",            # required
  "level": 100,
  "nature": "jolly",
  "evs": {"atk": 252, ...},    # default 0
  "ivs": {"atk": 31, ...},     # default 31
  "boosts": {"atk": 1, ...},   # -6..+6
  "item": "choiceband",
  "ability": "roughskin",      # overrides slot-0 default (graph lookup: HAS_ABILITY slot '0')
  "status": "brn",             # brn/par/psn/tox/slp/frz
  "tera_type": "dragon",
  "gender": "m",               # m/f (Rivalry)
  "hp_fraction": 1.0,          # Multiscale / Shadow Shield
  "weight_kg": 95.0            # required for Heavy Slam, Heat Crash, Low Kick, Grass Knot
}
field = {
  "weather": "sun|rain|sand|snow|harshsunlight|heavyrain|strongwinds",
  "terrain": "electric|grassy|misty|psychic",
  "is_grounded": {"attacker": True, "defender": True},   # default both True
  "screens": {"defender": ["reflect"|"lightscreen"|"auroraveil"]},
  "helping_hand": False,
  "is_spread": False           # caller-controlled; NOT inferred from move target
}
```

`level` of the defender is read from the defender dict independently (`def_level`).

### Pipeline (order matters - each step floors)

1. Load move (`base_power, category, type, target, priority`). `status` category -> `(0,0)`.
2. Resolve abilities (explicit dict value, else slot-0 ability), items, status, tera types, all lowercased.
3. Psychic Terrain + priority move + grounded defender -> `(0,0)`.
4. Move type = attacker's Tera type if move is `terablast` and attacker is Terastallized; else stored type.
5. Defender types = `[def_tera]` if Terastallized else graph types.
6. Stat selection:
   - Tera Blast (Terastallized): physical if the attacker's computed Atk >= SpA, else special.
   - Foul Play: uses the **defender's** Atk stat (with the defender's boosts/EVs/nature), physical.
   - Psyshock / Psystrike / Secret Sword: special move vs the defender's **Def**.
   - Otherwise physical -> Atk vs Def, special -> SpA vs SpD.
7. Stats via `calc_stat` + `apply_boost`. On a crit: attacker's negative boosts on the attacking stat are ignored; defender's positive boosts on the defending stat are ignored.
8. Stat multipliers (each `floor`):
   - Atk side: Choice Band x1.5, Gorilla Tactics x1.5, Guts x1.5 (if statused), Orichalcum Pulse x4/3 in sun.
   - SpA side: Choice Specs x1.5, Solar Power x1.5 in sun, Hadron Engine x4/3 in Electric Terrain (attacker grounded).
   - Defender Def: Eviolite x1.5. Defender SpD: Eviolite or Assault Vest x1.5. (These apply to whichever stat is the *defending* stat, so Psyshock is boosted by Eviolite but not Assault Vest.)
9. Effective base power (see variable BP table). If it resolves to 0 with no override, raise `ValueError` asking for `base_power_override`.
10. Weather multiplier: sun - Fire x1.5, Water x0.5; rain - Water x1.5, Fire x0.5; harsh sun makes Water 0 (immune); heavy rain makes Fire 0. 0 -> `(0,0)`.
11. Base damage: `floor(floor(2*level/5 + 2) * BP * Atk / Def / 50) + 2`
12. Spread: if `field.is_spread`, `floor(base * 0.75)`.
13. Weather: `floor(damage * w_mult)`.
14. Crit: `floor(damage * 1.5)` (Sniper: 2.25).
15. Roll: `[floor(damage * r / 100) for r in 85..100]` (16 values).
16. STAB (floor each roll):
    - no Tera: move type in attacker's types -> x1.5 (Adaptability x2.0), else 1.0
    - Tera, move type == Tera type: x2.0 if the Tera type is one of the original types; else x1.5 (Adaptability x2.0)
    - Tera, move type != Tera type: x1.0 *(see defect 1 in section 12 - this is wrong vs the real game)*
17. Type effectiveness, **one floor per defender type, sequentially**. Strong Winds: a Flying defender's weaknesses to Rock/Electric/Ice are clamped to 1x. Any 0.0 -> `(0,0)`. Track total `type_eff` product.
18. Wonder Guard: immune unless `type_eff > 1.0`.
19. Burn: x0.5 on physical moves (floored) unless Guts is active or the move is Foul Play.
20. Combined "final" multiplier (all multiplied together, then **one** floor per roll if final != 1.0):
    - Screens: Aurora Veil x0.5; Reflect x0.5 if physical; Light Screen x0.5 if special; none on a crit. (Singles value; no doubles 2/3.)
    - Helping Hand x1.5
    - Attacker items: Life Orb x1.3; Expert Belt x1.2 if `type_eff > 1`; Muscle Band x1.1 (physical); Wise Glasses x1.1 (special); type-boost items/plates/incenses x1.2 when the item's type equals the move type.
    - Attacker abilities: Technician x1.5 if effective BP <= 60; Iron Fist x1.2 (punch flag); Reckless x1.2 (recoil list); Sheer Force x1.3 (move has a secondary effect, detected by `"% chance"` in the description); Tough Claws x1.3 (contact flag); Tinted Lens x2.0 if `type_eff < 1`; Neuroforce x1.25 if `type_eff > 1`; Sand Force x1.3 (Rock/Steel/Ground in sand); Rivalry x1.25 same gender / x0.75 opposite (only when both genders given).
    - Defender abilities: Thick Fat x0.5 vs Fire/Ice; Fluffy x0.5 vs contact and x2.0 vs Fire; Punk Rock x0.5 vs sound; Ice Scales x0.5 vs special; Multiscale / Shadow Shield x0.5 at `hp_fraction >= 1.0`; Filter / Solid Rock / Prism Armor x0.75 if `type_eff > 1`.
    - Venoshock / Knock Off extra multiplier (see below).
    - Terrain (defender grounded): Electric Terrain x1.3 Electric; Grassy x1.3 Grass and x0.5 Earthquake/Bulldoze/Magnitude; Psychic x1.3 Psychic; Misty x0.5 Dragon.
21. Parental Bond: add a second hit of `floor(0.25 * first_hit_roll)` per roll.
22. Return `(min(rolls), max(rolls))`.


