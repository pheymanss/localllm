"""Pokemon stat calculation module."""

# 25-nature table (official Pokemon natures)
# Each nature boosts one stat by 10% (1.1) and reduces another by 10% (0.9)
# Hardy is neutral (no effect)
NATURE_TABLE = {
    "adamant": {"atk": 1.1, "def": 0.9},
    "bold": {"atk": 1.1, "spd": 0.9},
    "careful": {"def": 1.1, "spa": 0.9},
    "gentle": {"spa": 1.1, "spe": 0.9},
    "hardy": {},  # neutral nature (no effect)
    "hasty": {"atk": 1.1, "spd": 0.9},
    "happy": {"spd": 1.1, "spa": 0.9},
    "jolly": {"spe": 1.1, "atk": 0.9},
    "lonely": {"spd": 1.1, "def": 0.9},
    "mild": {"spa": 1.1, "def": 0.9},
    "naive": {"spe": 1.1, "atk": 0.9},
    "persevering": {"atk": 1.1, "spa": 0.9},
    "quiet": {"spa": 1.1, "spd": 0.9},
    "rash": {"spd": 1.1, "def": 0.9},
    "rivalous": {"atk": 1.1, "spe": 0.9},
    "sassy": {"spd": 1.1, "spa": 0.9},
    "sedate": {"spd": 1.1, "spe": 0.9},
    "timid": {"spe": 1.1, "def": 0.9},
}


def calc_stat(base, ev=0, iv=31, level=100, nature=None, stat_name=None):
    """Calculate a stat value based on the Pokemon stat formula.

    Args:
        base: Base stat value
        ev: Effort value (default 0)
        iv: Individual value (default 31, or None for default 31)
        level: Level of the Pokemon (default 100)
        nature: Nature name (e.g., "jolly", "adamant") or None
        stat_name: The stat to calculate ("atk", "def", "spa", "spd", "spe")

    Returns:
        int: Calculated stat value
    """
    # Handle default IV - iv=None means use 31, but explicit values (including 0) are used directly
    if iv is None:
        iv = 31
    
    # Calculate inner stat formula
    inner = ((2 * base + iv + (ev // 4)) * level // 100)
    
    # Determine nature_mod for this stat
    nature_mod = 1.0  # Default: neutral effect
    
    if nature is not None and nature in NATURE_TABLE:
        natures = NATURE_TABLE[nature]
        
        # Check if this stat matches the boosted stat (nature_mod = 1.1)
        if stat_name in natures.get("boosted", {}):
            nature_mod = 1.1
        # Check if this stat matches the reduced stat (nature_mod = 0.9)
        elif stat_name in natures.get("reduced", {}):
            nature_mod = 0.9
    
    # Calculate final stat value
    return ((inner + 5) * nature_mod).__int__()


def calc_hp(base, ev=0, iv=31, level=100):
    """Calculate HP based on the Pokemon HP formula.

    Args:
        base: Base HP value
        ev: Effort value (default 0)
        iv: Individual value (default 31)
        level: Level of the Pokemon (default 100)

    Returns:
        int: Calculated HP value
    """
    # Handle default IV - iv=None means use 31, but explicit values (including 0) are used directly
    if iv is None:
        iv = 31
    
    # Calculate inner part of HP formula
    hp_base = ((2 * base + iv + (ev // 4)) * level // 100)
    
    # HP formula adds level and 10 to the base calculation
    return hp_base + level + 10


def apply_boost(stat, boost, ignore_negative=False, ignore_positive=False):
    """Apply a stat modifier based on the battle boost value.

    Args:
        stat: The base stat value to boost
        boost: Boost value (-6 to 6), positive for attacker benefit, negative for defender
        ignore_negative: If True and boost < 0, treat as 0 (attacker on crit)
        ignore_positive: If True and boost > 0, treat as 0 (defender on crit)

    Returns:
        int: The boosted stat value
    """
    # Clamp boost to valid range [-6, 6]
    if boost < -6:
        boost = -6
    elif boost > 6:
        boost = 6
    
    # Handle ignore_negative for attacker critical hit (boost becomes 0)
    if ignore_negative and boost < 0:
        boost = 0
    
    # Handle ignore_positive for defender critical hit (boost becomes 0)
    if ignore_positive and boost > 0:
        boost = 0
    
    # Apply the appropriate formula based on positive or negative boost
    if boost > 0:
        return ((stat * (2 + boost)) // 2)
    elif boost < 0:
        return ((stat * 2) // (2 - boost))
    else:
        return stat
