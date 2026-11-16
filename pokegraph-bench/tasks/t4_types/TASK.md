# Task: Implement `type_matchup` and `coverage`

## How to work
- Python: run `python` (3.13; `kuzu`, `json5`, `pytest` installed). Do not pip install anything.
- Run tests with `python -m pytest -q`.
- `query/` is the import root: modules import each other by bare name (e.g. `from kuzu_conn import query`). Tests should add `query/` to `sys.path`.
- Write a few tests of your own in `tests/` and make them pass. Hidden tests will also be run against your code, using exactly the function names and signatures given below.
- Keep your context small: you do NOT need the rest of the spec. Everything you need is in this file.

Create `query/type_matchup.py` with `type_matchup(atk_type, defender_id) -> float` and `query/coverage.py` with `coverage(move_list, target_id) -> dict`, using the graph through `kuzu_conn.query`.

## Provided: `query/kuzu_conn.py`
- `query(cypher, params=None) -> list[list]` runs a read-only Cypher query on `graph/gen9.db` and returns all rows.
  Example: `query("MATCH (p:Pokemon {id:$id})-[h:HAS_TYPE]->(t:Type) RETURN t.name ORDER BY h.slot", {"id": "heatran"})` -> `[["fire"], ["steel"]]`.
- `get_conn()` returns the cached `kuzu.Connection` if you need it directly.

## 4. Graph schema (Kuzu)

### Node tables

| Node | Properties |
|---|---|
| `Pokemon` | id (PK), name, forme, base_species, tier, hp, atk, def, spa, spd, spe (all INT64 except strings) |
| `Move` | id (PK), name, type, category, base_power INT64, accuracy DOUBLE, priority INT64, pp INT64, target, description |
| `Ability` | id (PK), name, description |
| `Item` | id (PK), name, description |
| `Type` | name (PK) - exactly 18 nodes |
| `Nature` | name (PK), boosted_stat, reduced_stat (empty string for neutral) |

`accuracy = -1.0` means the move never misses (stored this way because the source value is boolean `true`).

### Relationship tables

| Edge | From -> To | Attributes |
|---|---|---|
| `HAS_TYPE` | Pokemon -> Type | `slot` INT64 (1 or 2) |
| `HAS_ABILITY` | Pokemon -> Ability | `slot` STRING (`"0"`, `"1"`, `"H"`) |
| `CAN_LEARN` | Pokemon -> Move | none |
| `IS_TYPE` | Move -> Type | none |
| `EFFECTIVE_VS` | Type -> Type | `multiplier` DOUBLE |

**`EFFECTIVE_VS` stores only non-neutral matchups.** Absence of an edge means 1x. Immunity is an edge with multiplier `0.0`. Direction is attacker -> defender.

### Critical convention: lowercase values

Every string *value* stored in the graph is lowercase: `category` is `'status'`/`'physical'`/`'special'`, type names are `'fire'`, etc. A filter on `'Status'` returns an empty result that is indistinguishable from "no data". This exact bug once caused a model to report that Gholdengo cannot learn Nasty Plot. Typed tools exist to make that class of error impossible.


## 6. `type_matchup(atk_type, defender_id) -> float`

Load the defender's types from `HAS_TYPE`. Start at 1.0; for each defender type multiply by the `EFFECTIVE_VS` multiplier if the edge exists. Raise `ValueError("Pokemon not found: ...")` if the defender has no types.

Examples: ground vs heatran = 4.0; ground vs skarmory = 0.0; fire vs corviknight = 2.0; dragon vs garchomp = 2.0; electric vs rotomwash = 1.0 (0.5 x 2.0); normal vs gengar = 0.0.

Tera is not handled here; Tera is handled in `damage_calc` via the defender dict.

## 7. `coverage(move_list, target_id) -> dict`

For each move id: look up `type` and `category`. Status moves get `{"move_type", "mult": None, "status_move": True}` and are excluded from the best. Unknown moves get `{"mult": None, "error": "move not found"}`. Otherwise `mult` is the product of `EFFECTIVE_VS` over the target's types. Variable-power moves (base_power 0) are still included by type.

Return:
```
{"best_mult": float|None, "best_moves": [ids with mult == best], "by_move": {id: {...}}}
```
`best_mult` is `None` and `best_moves` empty if no damaging move is present.

Reference checks, Garchomp moves `[earthquake, stoneedge, firepunch, swordsdance]`: vs skarmory best 2.0 (stoneedge); vs heatran 4.0 (earthquake); vs corviknight 2.0 (firepunch); vs toxapex 2.0 (earthquake). `coverage(["earthquake"], "skarmory")` -> 0.0.
