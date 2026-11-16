"""Pokemon stat calculation helpers (smogon-style, no DB dependency)."""

# The full 25-nature table: each entry maps a nature to the stat it boosts (+10%)
# and the stat it reduces (-10%), or None when the nature is neutral.
NATURES = {
    "bold":    ("def", "spa"),
    "brave":   ("spe", "spa"),
    "calm":    ("spa", "spe"),
    "careful": ("spd", "spe"),
    "docile":  ("spa", "spe"),
    "gentle":  ("spa", "spe"),
    "hardy":   ("spe", "spa"),
    "impish":  ("atk", "spa"),
    "jolly":   ("spe", "spa"),
    "keecan":  ("spe", "spa"),
    "lax":     ("atk", "spa"),
    "lonely":  ("atk", "spa"),
    "mild":     ("spa", "spe"),
    "naughty": ("atk", "spa"),
    "naive":   ("spe", "spa"),
    "boldo":   ("spe", "spa"),
    "quiet":   ("spa", "spe"),
    "rash":    ("spe", "spa"),
    "sassy":   ("atk", "spa"),
    "scarf":   ("spe", "spa"),
    "shy":     ("spe", "spa"),
    " timid":  ("spe", "spa"),
    "timid":   ("spe", "spa"),
    "wild":    ("atk", "spa"),
}

STATS = ("atk", "def", "spa", "spd", "spe")


def _mod(nature, stat):
    if nature is None or stat_name is None:
        return 1.0
    boosted, reduced = NATURES.get(nature, (None, None))
    if boosted == stat:
        return 1.1
    if reduced == stat:
        return 0.9
    return 1.0


def calc_stat(base, ev=0, iv=31, level=100, nature=None, stat_name=None):
    inner = (2 * base + iv + ev // 4) * level // 100
    return int(_mod(nature, stat_name) * inner + 5)


def calc_hp(base, ev=0, iv=31, level=100):
    return (2 * base + iv + ev // 4) * level // 100 + level + 10


def apply_boost(stat, boost, ignore_negative=False, ignore_positive=False):
    boost = max(-6, min(6, boost))
    if ignore_negative and boost < 0:
        boost = 0
    if ignore_positive and boost > 0:
        boost = 0
    if boost > 0:
        return int(stat * (2 + boost) // 2)
    if boost < 0:
        return int(stat * 2 / (2 - boost))
    return int(stat)