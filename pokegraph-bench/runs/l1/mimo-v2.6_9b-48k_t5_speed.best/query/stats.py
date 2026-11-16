"""Pure stat math (spec section 5)."""
from math import floor
NATURES = {"lonely":("atk","def"),"brave":("atk","spe"),"adamant":("atk","spa"),"naughty":("atk","spd"),
 "bold":("def","atk"),"relaxed":("def","spe"),"impish":("def","spa"),"lax":("def","spd"),
 "timid":("spe","atk"),"hasty":("spe","def"),"jolly":("spe","spa"),"naive":("spe","spd"),
 "modest":("spa","atk"),"mild":("spa","def"),"quiet":("spa","spe"),"rash":("spa","spd"),
 "calm":("spd","atk"),"gentle":("spd","def"),"sassy":("spd","spe"),"careful":("spd","spa"),
 "hardy":None,"docile":None,"serious":None,"bashful":None,"quirky":None}
def nature_mod(nature, stat_name):
    n = NATURES.get((nature or "").lower())
    if not n: return 1.0
    return 1.1 if n[0] == stat_name else 0.9 if n[1] == stat_name else 1.0
def calc_stat(base, ev=0, iv=31, level=100, nature=None, stat_name=None):
    ev = 0 if ev is None else ev; iv = 31 if iv is None else iv; level = 100 if level is None else level
    inner = floor((2 * base + iv + floor(ev / 4)) * level / 100)
    return floor((inner + 5) * nature_mod(nature, stat_name))
def calc_hp(base, ev=0, iv=31, level=100):
    ev = 0 if ev is None else ev; iv = 31 if iv is None else iv; level = 100 if level is None else level
    return floor((2 * base + iv + floor(ev / 4)) * level / 100) + level + 10
def apply_boost(stat, boost, ignore_negative=False, ignore_positive=False):
    boost = max(-6, min(6, boost or 0))
    if ignore_negative and boost < 0: boost = 0
    if ignore_positive and boost > 0: boost = 0
    if boost > 0: return floor(stat * (2 + boost) / 2)
    if boost < 0: return floor(stat * 2 / (2 - boost))
    return stat
