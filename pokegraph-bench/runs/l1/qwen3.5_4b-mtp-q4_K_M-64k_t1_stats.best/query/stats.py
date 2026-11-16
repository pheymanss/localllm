"""Pokemon stat calculations."""

# Full nature table: 25 natures, each with {boosted_stat: 1.1, reduced_stat: 0.9}
# Neutral natures (adamant, timid) have empty dicts
NATURES = {
    "bold": {"def": 1.1, "spa": 0.9}, "jolly": {"spd": 1.1, "spe": 0.9}, "hasty": {"atk": 1.1, "def": 0.9},
    "quiet": {"atk": 1.1, "spa": 0.9}, "mild": {"spa": 1.1, "def": 0.9}, "modest": {"spa": 1.1, "atk": 0.9},
    "rash": {"spd": 1.1, "atk": 0.9}, "adamant": {"atk": 1.1, "def": 0.9}, "naive": {"spd": 1.1, "spa": 0.9},
    "happier": {"spd": 1.1, "spe": 0.9}, "careful": {"def": 1.1, "atk": 0.9}, "quiet": {"atk": 1.1, "spa": 0.9},
    "sassy": {"spd": 1.1, "spa": 0.9}, "impudent": {"spe": 1.1, "atk": 0.9}, "docile": {"spa": 1.1, "def": 0.9},
    "soft": {"spd": 1.1, "atk": 0.9}, "mild": {"spa": 1.1, "def": 0.9}, "relaxed": {"atk": 1.1, "def": 0.9},
    "silly": {"spe": 1.1, "spa": 0.9}, "gentle": {"spd": 1.1, "atk": 0.9}, "rival": {"atk": 1.1, "def": 0.9},
}


def calc_stat(base, ev=0, iv=31, level=100, nature=None, stat_name=None):
    """Calculate a Pokemon's base stat after EV/IV boost and nature effect."""
    if nature is None:
        nature_mod = 1.0
    else:
        nature_dict = NATURES[nature]
        if stat_name in nature_dict and "boosted" in nature_dict:
            nature_mod = nature_dict["boosted"]
        elif stat_name in nature_dict and "reduced" in nature_dict:
            nature_mod = 0.9
        else:
            nature_mod = 1.0

    inner = int((2 * base + iv + (ev // 4)) * level / 100)
    return int((inner + 5) * nature_mod)


def calc_hp(base, ev=0, iv=31, level=100):
    """Calculate a Pokemon's HP."""
    inner = int((2 * base + iv + (ev // 4)) * level / 100)
    return int(inner + level + 10)


def apply_boost(stat, boost, ignore_negative=False, ignore_positive=False):
    """Apply an attack boost value to a stat."""
    if not (-6 <= boost <= 6):
        raise ValueError(f"Boost must be between -6 and 6, got {boost}")
    
    if ignore_negative and boost < 0:
        boost = 0
    if ignore_positive and boost > 0:
        boost = 0
    
    if boost > 0:
        return int(stat * (2 + boost) / 2)
    elif boost < 0:
        return int(stat * 2 / (2 - boost))
    else:
        return stat
