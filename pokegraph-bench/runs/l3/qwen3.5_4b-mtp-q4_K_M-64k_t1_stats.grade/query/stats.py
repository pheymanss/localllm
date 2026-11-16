"""Stat calculations for Pokemon."""

# Full 25-nature table (lowercase keys) - Gen 6+ nature list with duplicates included
NATURES = {
    "hardy": {}, "adamant": {"atk": 1.1, "def": 0.9}, "impartial": {"spd": 1.1, "atk": 0.9},
    "bold": {"def": 1.1, "atk": 0.9}, "modest": {"spa": 1.1, "def": 0.9}, "quiet": {"def": 1.1, "spa": 0.9},
    "careful": {"atk": 1.1, "spd": 0.9}, "hasty": {"atk": 1.1, "spa": 0.9}, "naive": {"spa": 1.1, "atk": 0.9},
    "rash": {"spd": 1.1, "def": 0.9}, "relaxed": {"def": 1.1, "spd": 0.9}, "sassy": {"spd": 1.1, "atk": 0.9},
    "gentle": {"spa": 1.1, "spd": 0.9}, "jolly": {"spe": 1.1, "atk": 0.9}, "mild": {"spa": 1.1, "spd": 0.9},
    "naive": {"spa": 1.1, "atk": 0.9}, "brave": {"atk": 1.1, "spd": 0.9}, "modest": {"spa": 1.1, "def": 0.9},
    "quiet": {"def": 1.1, "spa": 0.9}, "hasty": {"atk": 1.1, "spa": 0.9}, "careful": {"atk": 1.1, "spd": 0.9},
    "relaxed": {"def": 1.1, "spd": 0.9}, "sassy": {"spd": 1.1, "atk": 0.9}, "impish": {"atk": 1.1, "spa": 0.9},
    "lonely": {"atk": 1.1, "spa": 0.9}, "bold": {"def": 1.1, "atk": 0.9}, "naive": {"spa": 1.1, "atk": 0.9},
    "mild": {"spa": 1.1, "spd": 0.9}, "gentle": {"spa": 1.1, "spd": 0.9}, "timid": {"spe": 1.1, "atk": 0.9}
}


def calc_stat(base, ev=0, iv=31, level=100, nature=None, stat_name=None):
    """Calculate a base stat with EVs, IVs, level, and nature."""
    # Handle None IV as default 31 (explicit 0 must be respected)
    if iv is None:
        iv = 31
    
    inner = (2 * base + iv + (ev // 4)) * level / 100
    inner = int(inner)
    
    # Get nature modifier
    if nature is None:
        nature_mod = 1.0
    else:
        nature_mod = NATURES[nature].get(stat_name, 1.0)
    
    # Apply nature modifier
    stat = (inner + 5) * nature_mod
    return int(stat)


def calc_hp(base, ev=0, iv=31, level=100):
    """Calculate HP."""
    if iv is None:
        iv = 31
    inner = (2 * base + iv + (ev // 4)) * level / 100
    inner = int(inner)
    return int(inner) + level + 10


def apply_boost(stat, boost, ignore_negative=False, ignore_positive=False):
    """Apply a stat boost or reduction."""
    # Clamp boost to valid range
    if boost < -6:
        boost = -6
    if boost > 6:
        boost = 6
    
    # Handle ignore flags
    if ignore_negative and boost < 0:
        boost = 0
    if ignore_positive and boost > 0:
        boost = 0
    
    # Apply boost/reduction
    if boost > 0:
        return int(stat * (2 + boost) / 2)
    elif boost < 0:
        return int(stat * 2 / (2 - boost))
    else:
        return stat
