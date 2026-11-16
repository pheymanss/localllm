"""Reference ETL. usage: python etl.py <raw_dir|URL> <knowledge_dir>"""
import json, os, re, sys, urllib.request
import json5
BASE = "https://play.pokemonshowdown.com/data/"
BAD = {"Past", "Unobtainable", "CAP", "LGPE"}
TYPES = ["normal","fire","water","electric","grass","ice","fighting","poison","ground","flying","psychic","bug","rock","ghost","dragon","dark","steel","fairy"]
def norm(s): return re.sub(r"[^a-z0-9]", "", s.lower())
def load(src, name):
    if src.startswith("http"):
        req = urllib.request.Request(BASE + name + ".js", headers={"User-Agent": "Mozilla/5.0"})
        txt = urllib.request.urlopen(req).read().decode()
    else:
        txt = open(os.path.join(src, name + ".js")).read()
    return json5.loads(txt[txt.index("{"): txt.rindex("}") + 1])
NATURES = {"hardy":(None,None),"lonely":("atk","def"),"brave":("atk","spe"),"adamant":("atk","spa"),"naughty":("atk","spd"),
 "bold":("def","atk"),"docile":(None,None),"relaxed":("def","spe"),"impish":("def","spa"),"lax":("def","spd"),
 "timid":("spe","atk"),"hasty":("spe","def"),"serious":(None,None),"jolly":("spe","spa"),"naive":("spe","spd"),
 "modest":("spa","atk"),"mild":("spa","def"),"quiet":("spa","spe"),"bashful":(None,None),"rash":("spa","spd"),
 "calm":("spd","atk"),"gentle":("spd","def"),"sassy":("spd","spe"),"careful":("spd","spa"),"quirky":(None,None)}
def main(src, out):
    os.makedirs(os.path.join(out, "pokemon"), exist_ok=True)
    w = lambda n, d: json.dump(d, open(os.path.join(out, n), "w"), indent=1, sort_keys=True)
    tc = load(src, "typechart"); chart = {}
    for dt, v in tc.items():
        if dt not in TYPES: continue
        row = {}
        for at, code in v["damageTaken"].items():
            if at.lower() not in TYPES or code == 0: continue
            row[at.lower()] = {1: 2.0, 2: 0.5, 3: 0.0}[code]
        chart[dt] = row
    w("type_chart.json", chart)
    w("natures.json", {k: {"boosted": b, "reduced": r} for k, (b, r) in NATURES.items()})
    for name in ("items", "abilities"):
        d = load(src, name)
        w(name + ".json", {k: {"name": v["name"], "desc": v.get("desc") or v.get("shortDesc", ""), "gen": v.get("gen")}
                           for k, v in d.items() if v.get("isNonstandard") not in BAD and k != "noability"})
    mv = load(src, "moves"); moves = {}
    for k, v in mv.items():
        if v.get("isNonstandard") in BAD: continue
        moves[k] = {"name": v["name"], "type": v["type"].lower(), "category": v["category"].lower(),
                    "base_power": v.get("basePower", 0), "accuracy": v["accuracy"], "priority": v.get("priority", 0),
                    "pp": v.get("pp", 0), "target": v.get("target", ""), "flags": v.get("flags", {}), "desc": v.get("shortDesc", "")}
    w("moves.json", moves)
    ls = load(src, "learnsets"); learn = {}
    for k, v in ls.items():
        ms = sorted(m for m, srcs in (v.get("learnset") or {}).items() if any(s.startswith("9") for s in srcs))
        if ms: learn[k] = ms
    w("learnsets.json", learn)
    dex = load(src, "pokedex"); n = 0
    for k, v in dex.items():
        if v.get("isNonstandard") in {"CAP", "LGPE", "Unobtainable"} or "baseStats" not in v or "types" not in v: continue
        rec = {"name": v["name"], "num": v.get("num", 0), "types": [t.lower() for t in v["types"]], "base_stats": v["baseStats"],
               "abilities": {s: norm(a) for s, a in v["abilities"].items()}, "tier": v.get("tier", ""),
               "forme": v.get("forme", ""), "base_species": v.get("baseSpecies", v["name"]), "learnset": learn.get(k, [])}
        json.dump(rec, open(os.path.join(out, "pokemon", k + ".json"), "w"), indent=1); n += 1
    print("pokemon:", n, "moves:", len(moves), "learnsets:", len(learn))
if __name__ == "__main__": main(sys.argv[1], sys.argv[2])
