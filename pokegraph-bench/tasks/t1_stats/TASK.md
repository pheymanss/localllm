# Task: Implement `query/stats.py`

## How to work
- Python: run `python` (3.13; `kuzu`, `json5`, `pytest` installed). Do not pip install anything.
- Run tests with `python -m pytest -q`.
- `query/` is the import root: modules import each other by bare name (e.g. `from kuzu_conn import query`). Tests should add `query/` to `sys.path`.
- Write a few tests of your own in `tests/` and make them pass. Hidden tests will also be run against your code, using exactly the function names and signatures given below.
- Keep your context small: you do NOT need the rest of the spec. Everything you need is in this file.

Create `query/stats.py` with exactly these functions:
- `calc_stat(base, ev=0, iv=31, level=100, nature=None, stat_name=None) -> int` (`nature` is a lowercase nature name such as `"jolly"` or None; `stat_name` is one of `atk def spa spd spe`)
- `calc_hp(base, ev=0, iv=31, level=100) -> int`
- `apply_boost(stat, boost, ignore_negative=False, ignore_positive=False) -> int`
Include the full 25-nature table inside `stats.py` (no DB, no files).

## 5. Stat math (`query/stats.py`, pure functions)

```
calc_stat(base, ev, iv, level, nature, stat_name):
    inner = floor((2*base + iv + floor(ev/4)) * level / 100)
    return floor((inner + 5) * nature_mod)          # nature_mod in {0.9, 1.0, 1.1}

calc_hp(base, ev, iv, level):
    return floor((2*base + iv + floor(ev/4)) * level / 100) + level + 10

apply_boost(stat, boost, ignore_negative=False, ignore_positive=False):
    boost = clamp(boost, -6, 6)
    if ignore_negative and boost < 0: boost = 0     # attacker on a crit
    if ignore_positive and boost > 0: boost = 0     # defender on a crit
    boost > 0: floor(stat * (2+boost) / 2)
    boost < 0: floor(stat * 2 / (2-boost))
```

Defaults: IV = 31, EV = 0, level = 100. `iv=None` means 31 (so an explicit IV of 0 must be respected - `0` is falsy, use `is not None`). Nature table: 25 natures, each `{boosted_stat: 1.1, reduced_stat: 0.9}`; neutral natures are empty.
