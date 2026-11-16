# Task: Implement `speed_check`

## How to work
- Python: run `python` (3.13; `kuzu`, `json5`, `pytest` installed). Do not pip install anything.
- Run tests with `python -m pytest -q`.
- `query/` is the import root: modules import each other by bare name (e.g. `from kuzu_conn import query`). Tests should add `query/` to `sys.path`.
- **The acceptance tests are already written: `tests/test_given.py`.** Your job is to make ALL of them pass. Do NOT edit `tests/test_given.py` or `conftest.py` (they are re-copied before grading). Read the test file first: it shows the exact function names, signatures and expected values.
- Run them with `python -m pytest -q tests/test_given.py` (from this directory). Fix your code, not the tests, until everything passes.
- Keep your context small: you do NOT need the rest of the spec. Everything you need is in this file.

Create `query/speed_check.py` with `speed_check(a, b, field=None) -> dict`. Read base Speed from the graph (`Pokemon.spe`).

## Provided: `query/kuzu_conn.py`
- `query(cypher, params=None) -> list[list]` runs a read-only Cypher query on `graph/gen9.db` and returns all rows.
  Example: `query("MATCH (p:Pokemon {id:$id})-[h:HAS_TYPE]->(t:Type) RETURN t.name ORDER BY h.slot", {"id": "heatran"})` -> `[["fire"], ["steel"]]`.
- `get_conn()` returns the cached `kuzu.Connection` if you need it directly.

## Provided: `query/stats.py`
`calc_stat(base, ev=0, iv=31, level=100, nature=None, stat_name=None)`, `calc_hp(base, ev=0, iv=31, level=100)`,
`apply_boost(stat, boost, ignore_negative=False, ignore_positive=False)`. `nature` is a lowercase nature name like `"jolly"`. Already correct; use it.

## 8. `speed_check(a, b, field=None) -> dict`

Each side: `{id, level=100, nature, evs, ivs, boosts, item, ability, status}`. Field: `{weather, terrain, tailwind: ["a"|"b", ...], trick_room: bool}`.

Computation order per side:
1. Base Speed from the graph, `calc_stat` with the side's EV/IV/nature/level, then `apply_boost` with `boosts["spe"]`.
2. Item: `choicescarf` -> floor(x1.5); `ironball` or `machobrace` -> floor(x0.5).
3. Ability (read ONLY from the side dict - **no default to slot-0 ability**):
   - `unburden` -> x2 (caller asserts the item was consumed)
   - weather abilities, x2 when active: `swiftswim` (rain), `chlorophyll` (sun), `sandrush` (sand), `slushrush` (snow), `surgesurfer` (electric *terrain*). `harshsunlight` counts as sun, `heavyrain` as rain.
4. Paralysis (`status == "par"`): floor(x0.5) (Gen 7+ value).
5. Tailwind: if the side's key (`"a"`/`"b"`) is in `field["tailwind"]`, floor(x2).

Result: `{"winner": "a"|"b"|"tie", "a_speed": int, "b_speed": int, "tied": bool}`. Ties are `"tie"` and are NOT broken. Trick Room inverts the comparison (lower speed wins) but a tie stays a tie.

Each multiplier is floored independently in the order above.
