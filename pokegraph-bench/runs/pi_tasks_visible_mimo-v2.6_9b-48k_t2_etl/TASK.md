# Task: Write the ETL `query/etl.py`

## How to work
- Python: run `python` (3.13; `kuzu`, `json5`, `pytest` installed). Do not pip install anything.
- Run tests with `python -m pytest -q`.
- `query/` is the import root: modules import each other by bare name (e.g. `from kuzu_conn import query`). Tests should add `query/` to `sys.path`.
- **The acceptance tests are already written: `tests/test_given.py`.** Your job is to make ALL of them pass. Do NOT edit `tests/test_given.py` or `conftest.py` (they are re-copied before grading). Read the test file first: it shows the exact function names, signatures and expected values.
- Run them with `python -m pytest -q tests/test_given.py` (from this directory). Fix your code, not the tests, until everything passes.
- Keep your context small: you do NOT need the rest of the spec. Everything you need is in this file.

Create `query/etl.py` with a function `build(source_dir, out_dir)` and a CLI: `python query/etl.py raw knowledge`.
The six Showdown files are already downloaded into `raw/` (`typechart.js items.js abilities.js moves.js learnsets.js pokedex.js`), so read them from `source_dir` instead of fetching.
Write the 7 outputs into `out_dir`: `type_chart.json natures.json items.json abilities.json moves.json learnsets.json` and `pokemon/<id>.json`.
Notes: `raw/pokedex.js` is large (~450 KB) and `raw/learnsets.js` is ~3 MB: do not print or read them whole; inspect with `head -c` or small Python snippets. These client files have no `desc`/`shortDesc` on moves/items/abilities, so those fields may be empty strings. Some pokedex entries lack `num`; handle that gracefully.
Type chart: only the 18 real types are keys; Showdown `damageTaken` also contains non-type keys (e.g. `prankster`, `par`, `sandstorm`, `powder`) which must be skipped.

## 3. Data pipeline (ETL)

Source: Pokemon Showdown's public data files at `https://play.pokemonshowdown.com/data/` - `typechart.js`, `items.js`, `abilities.js`, `moves.js`, `learnsets.js`, `pokedex.js`.

These are JavaScript object literals (`exports.BattlePokedex = { bulbasaur: {...}, ... };`), not JSON. The ETL slices from the first `{` to the last `}` and parses with `json5` (handles unquoted keys). A `User-Agent: Mozilla/5.0` header is required.

Transformations:

| Output | Rule |
|---|---|
| `type_chart.json` | Showdown `damageTaken` codes: 0=1x (skipped), 1=2x, 2=0.5x, 3=0x. Stored as `{defending: {attacking: mult}}`, all lowercased. The `Stellar` key is skipped. |
| `natures.json` | Hardcoded 25 natures: `{name: {"boosted": stat\|None, "reduced": stat\|None}}`. Five neutral natures (hardy, docile, serious, bashful, quirky) have both None. |
| `items.json`, `abilities.json` | Drop entries where `isNonstandard` in {Past, Unobtainable, CAP, LGPE}. Keep `name`, `desc` (falls back to `shortDesc`), `gen`. |
| `moves.json` | Same `isNonstandard` filter. Keep name, `type` (lowercased), `category` (lowercased: `physical`/`special`/`status`), `base_power`, `accuracy` (`true` = never misses), `priority`, `pp`, `target`, `flags` (dict, e.g. `{"contact":1,"punch":1}`), `desc` (shortDesc). |
| `learnsets.json` | Keep a move only if any of its source strings starts with `9` (learnable in Gen 9). Sorted list per species. Species with no Gen 9 moves are omitted. |
| `pokemon/<id>.json` | Skip `isNonstandard` in {CAP, LGPE, Unobtainable}. Fields: name, num, types (lowercased list), base_stats, abilities (`{slot: ability_id}`, ids lowercased with spaces removed), tier, forme, base_species, learnset. |

ID convention everywhere: **lowercase, alphanumerics only** - `greattusk`, `landorustherian`, `makeitrain`, `rotomwash`. Normalizer: `re.sub(r"[^a-z0-9]", "", s.lower())`.
