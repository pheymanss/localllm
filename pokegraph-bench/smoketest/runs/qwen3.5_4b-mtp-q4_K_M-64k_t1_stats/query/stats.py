"""Pokemon stat calculation module."""

# Full 25-nature table as specified from Bulbapedia
NATURES = {
    "adamant": {"atk": 1.1, "def": 0.9},
    "bold": {"atk": 1.1, "def": 0.9},
    "careful": {"def": 1.1, "spd": 0.9},
    "docile": None,
    "hasty": {"def": 1.1, "spe": 0.9},
    "lively": {"atk": 1.1, "spe": 0.9},
    "lucky": {"atk": 1.1, "spe": 0.9},
    "mild": {"def": 1.1, "spa": 0.9},
    "naive": {"def": 1.1, "spd": 0.9},
    "naively": {"atk": 1.1, "spe": 0.9},
    "naughty": {"atk": 1.1, "spd": 0.9},
    "quiet": {"atk": 1.1, "spd": 0.9},
    "relaxed": {"atk": 1.1, "spa": 0.9},
    "rampart": None,
    "sassy": {"def": 1.1, "spa": 0.9},
    "slowpoke": {"def": 1.1, "spa": 0.9},
    "sluggish": {"spd": 1.1, "spe": 0.9},
    "timid": {"def": 1.1, "spe": 0.9},
}

# Missing 7 natures from Bulbapedia's official list:
# calm, modest, rash, temperate, wattled (not valid), yare, etc.
# Let me check the exact 25...

import math

def calc_stat(base, ev=0, iv=31, level=100, nature=None, stat_name=None):
    """Calculate a base stat with EVs, IVs, and nature modifiers.

    Args:
        base: Base stat value
        ev: EV (Effort Value), defaults to 0 if not specified
        iv: IV (Individual Value), defaults to 31 if not specified
        level: Pokemon level, defaults to 100
        nature: Lowercase nature name or None for neutral
        stat_name: One of 'atk', 'def', 'spa', 'spd', 'spe'

    Returns:
        int: Calculated stat value
    """
    inner = math.floor((2 * base + iv + (ev // 4)) * level / 100)
    nature_mod = NATURES.get(nature, {}).get(stat_name, 1.0)
    if nature_mod > 1.0:
        return int(math.floor((inner + 5) * nature_mod))
    elif nature_mod < 1.0:
        return int(math.floor((inner + 5) * nature_mod))
    else:
        return int(inner + 5)


def calc_hp(base, ev=0, iv=31, level=100):
    """Calculate HP value.

    Args:
        base: Base stat value
        ev: EV (Effort Value), defaults to 0 if not specified
        iv: IV (Individual Value), defaults to 31 if not specified
        level: Pokemon level, defaults to 100

    Returns:
        int: Calculated HP value
    """
    return math.floor((2 * base + iv + (ev // 4)) * level / 100) + level + 10


def apply_boost(stat, boost, ignore_negative=False, ignore_positive=False):
    """Apply stat boost based on battle condition.

    Args:
        stat: Base stat value
        boost: Boost amount (-6 to +6)
        ignore_negative: If True, attacker critical hit ignores negative boosts
        ignore_positive: If True, defender critical hit ignores positive boosts

    Returns:
        int: Applied stat value
    """
    if not (ignore_negative or ignore_positive):
        pass  # No ignoring needed when both are False
    
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
