"""Pokemon stat calculation helpers (pure functions, no DB)."""

# Full 25-nature table: {name: {boosted_stat: 1.1, reduced_stat: 0.9}}
# Neutral natures have an empty multiplier dict.
NATURES = {
    "adamant": {"atk": 1.1, "spa": 0.9},
    "bold": {"def": 1.1, "spa": 0.9},
    "brisk": {"spe": 1.1, "spd": 0.9},
    "calm": {"spd": 1.1, "spe": 0.9},
    "careful": {"def": 1.1, "spe": 0.9},
    "docile": {},
    "gentle": {"spa": 1.1, "spe": 0.9},
    "hardy": {"spe": 1.1, "def": 0.9},
    "impish": {"spa": 1.1, "spd": 0.9},
    "jolly": {"spe": 1.1, "atk": 0.9},
    "loud": {"atk": 1.1, "spe": 0.9},
    "modest": {"spa": 1.1, "atk": 0.9},
    "mild": {"def": 1.1, "atk": 0.9},
    "naive": {"spa": 1.1, "def": 0.9},
    "naughty": {"atk": 1.1, "def": 0.9},
    "relaxed": {"spe": 1.1, "spd": 0.9},
    "rash": {"spa": 1.1, "spe": 0.9},
    "sassy": {"def": 1.1, "spe": 0.9},
    "slow": {"spd": 1.1, "spe": 0.9},
    "snug": {"def": 1.1, "spe": 0.9},
    "stubborn": {"spa": 1.1, "spe": 0.9},
    "timid": {"spe": 1.1, "spd": 0.9},
    "quiet": {"spa": 1.1, "spe": 0.9},
    "curious": {"def": 1.1, "spd": 0.9},
}

STAT_KEYS = ("atk", "def", "spa", "spd", "spe")


def calc_stat(base, ev=0, iv=31, level=100, nature=None, stat_name=None):
    """Calculate a stat at a given level, IVs, EVs and optional nature."""
    inner = (2 * base + (iv if iv is not None else 31) + ev // 4) * level // 100
    # Nature multipliers are exact fractions: x1.1 -> *11//10, x0.9 -> *9//10.
    for stat_key, mult in (NATURES[nature] if nature else {}).items():
        if mult > 1.0 and stat_key == stat_name:
            inner = (inner + 5) * int(mult * 10) // 10
            break
    else:
        inner += 5
    return inner


def calc_hp(base, ev=0, iv=31, level=100):
    """Calculate HP (HP ignores nature modifiers)."""
    return (2 * base + (iv if iv is not None else 31) + ev // 4) * level // 100 + level + 10


def apply_boost(stat, boost, ignore_negative=False, ignore_positive=False):
    """Apply a stage boost (-6..6) to a stat."""
    if boost < 0 and ignore_negative:
        boost = 0
    if boost > 0 and ignore_positive:
        boost = 0
    boost = max(-6, min(6, boost))
    if boost > 0:
        return stat * (2 + boost) // 2
    if boost < 0:
        return stat * 2 // (2 - boost)
    return stat