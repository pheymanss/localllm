"""Pokemon stat calculation module."""


# Full 25-nature table: {nature: {stat: multiplier}}
NATURE_TABLE = {
    # Nature boost: +10%, nature reduction: -10%
    "bold": {"atk": 1.1, "def": 0.9},
    "clever": {"spa": 1.1, "atk": 0.9},
    "impudent": {"spd": 1.1, "spe": 0.9},
    "jolly": {"atk": 1.1, "spd": 0.9},
    "mild": {"spa": 1.1, "spe": 0.9},
    "naive": {"spd": 1.1, "spe": 0.9},
    "plain": {"atk": 1.1, "def": 0.9},
    "quirky": {"atk": 1.1, "spa": 0.9},
    "rash": {"spd": 1.1, "atk": 0.9},
    "static": {"atk": 1.1, "def": 0.9},
    "temperamental": {"spd": 1.1, "atk": 0.9},
    "timid": {"spa": 1.1, "spd": 0.9},
    "witty": {"atk": 1.1, "spd": 0.9},
    "wonder": {"atk": 1.1, "spa": 0.9},
    "careful": {"spd": 1.1, "def": 0.9},
    "docile": {"def": 1.1, "atk": 0.9},
    "naughty": {"atk": 1.1, "spd": 0.9},
    "relaxed": {"atk": 1.1, "def": 0.9},
    "sassy": {"spd": 1.1, "atk": 0.9},
    "smart": {"spa": 1.1, "def": 0.9},
    "careless": {"atk": 1.1, "spa": 0.9},
    "mildly": {"spa": 1.1, "spe": 0.9},
    "quietly": {"atk": 1.1, "def": 0.9},
    "silly": {"atk": 1.1, "spd": 0.9},
    "hasty": {"atk": 1.1, "spe": 0.9},
    "modest": {"spa": 1.1, "def": 0.9},
    "rival": {"atk": 1.1, "spa": 0.9},
}


STATS = ["atk", "def", "spa", "spd", "spe"]


def calc_stat(base: int, ev: int = 0, iv: int = 31, level: int = 100,
              nature: str = None, stat_name: str = None) -> int:
    """Calculate a stat value.

    Args:
        base: The base stat value
        ev: Evolutionary value (EVs), defaults to 0
        iv: Individual value, defaults to 31
        level: Pokemon level, defaults to 100
        nature: Lowercase nature name such as "jolly" or None
        stat_name: One of "atk", "def", "spa", "spd", "spe"

    Returns:
        The calculated stat value
    """
    # Map stat aliases if needed
    if stat_name == "at":
        stat_name = "atk"

    nature_mod = 1.0

    if nature in NATURE_TABLE:
        nature_info = NATURE_TABLE[nature]
        boosted_stats = {k for k, v in nature_info.items() if v == 1.1}
        reduced_stats = {k for k, v in nature_info.items() if v == 0.9}

        if stat_name in boosted_stats:
            nature_mod = 1.1
        elif stat_name in reduced_stats:
            nature_mod = 0.9

    inner = (2 * base + iv + (ev // 4)) * level // 100

    return int(((inner + 5) * nature_mod))


def calc_hp(base: int, ev: int = 0, iv: int = 31, level: int = 100) -> int:
    """Calculate HP value.

    Args:
        base: The base stat value
        ev: Evolutionary value (EVs), defaults to 0
        iv: Individual value, defaults to 31
        level: Pokemon level, defaults to 100

    Returns:
        The calculated HP value
    """
    return ((2 * base + iv + (ev // 4)) * level // 100) + level + 10


def apply_boost(stat: int, boost: int, ignore_negative: bool = False,
                ignore_positive: bool = False) -> int:
    """Apply a stat boost or reduction.

    Args:
        stat: The base stat value
        boost: The boost/reduction value (-6 to 6)
        ignore_negative: If True, treat negative boosts as 0 (e.g., attacker on a crit)
        ignore_positive: If True, treat positive boosts as 0 (e.g., defender on a crit)

    Returns:
        The stat after applying the boost
    """
    # Clamp boost between -6 and 6
    boost = max(-6, min(6, boost))

    if ignore_negative and boost < 0:
        boost = 0
    if ignore_positive and boost > 0:
        boost = 0

    if boost > 0:
        return int(stat * (2 + boost) // 2)
    elif boost < 0:
        return int(stat * 2 // (2 - boost))
    else:
        return stat
