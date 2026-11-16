NATURES = {
    "gentle": {"spa": 1.1, "spd": 0.9},
    "hardy": {},
    "jolly": {"spe": 1.1, "atk": 0.9},
    "naive": {"spe": 1.1, "spa": 0.9},
    "timid": {"spe": 1.1, "spd": 0.9},
    "adamant": {"atk": 1.1, "spa": 0.9},
    "modest": {"spa": 1.1, "atk": 0.9},
    "quiet": {"spe": 1.1, "def": 0.9},
    "relaxed": {"spd": 1.1, "atk": 0.9},
    "bold": {"spe": 1.1, "def": 0.9},
    "impish": {"atk": 1.1, "spa": 0.9},
    "luxury": {"spd": 1.1, "spe": 0.9},
    "docile": {"spa": 1.1, "spe": 0.9},
    "naughty": {"spe": 1.1, "spa": 0.9},
    "serious": {},
    "sassy": {"spd": 1.1, "spa": 0.9},
    "quirky": {"spe": 1.1, "spa": 0.9},
    "rush": {"spe": 1.1, "spa": 0.9},
}

STATS = ("atk", "def", "spa", "spd", "spe")


def calc_stat(base, ev=0, iv=None, level=100, nature=None, stat_name=None):
    if iv is None:
        iv = 31
    inner = int((2 * base + iv + int(ev // 4)) * level // 100)
    mod = NATURES.get(nature, {}).get(stat_name, 1.0)
    return int((inner + 5) * mod // 1)


def calc_hp(base, ev=0, iv=None, level=100):
    if iv is None:
        iv = 31
    return int((2 * base + iv + int(ev // 4)) * level // 100) + level + 10


def apply_boost(stat, boost, ignore_negative=False, ignore_positive=False):
    if boost < -6:
        boost = -6
    elif boost > 6:
        boost = 6
    if ignore_negative and boost < 0:
        boost = 0
    if ignore_positive and boost > 0:
        boost = 0
    if boost > 0:
        return int(stat * (2 + boost) // 2)
    if boost < 0:
        return int(stat * 2 // (2 - boost))
    return int(stat)