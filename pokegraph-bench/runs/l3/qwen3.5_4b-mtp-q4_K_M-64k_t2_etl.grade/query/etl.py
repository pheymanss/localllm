#!/usr/bin/env python3
import sys, os, json, re, shutil
from pathlib import Path

def normalize(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())

import json5

def parse_js_file(path):
    with open(path) as f:
        content = f.read()
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1:
        return None
    js_content = content[start:end+1]
    return json5.loads(js_content, parse_float=repr)

def build(source_dir, out_dir):
    source_dir = Path(source_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "pokemon").mkdir(exist_ok=True)
    
    # Read all source files
    type_chart_data = parse_js_file(source_dir / "typechart.js")
    items_data = parse_js_file(source_dir / "items.js")
    abilities_data = parse_js_file(source_dir / "abilities.js")
    moves_data = parse_js_file(source_dir / "moves.js")
    learnsets_data = parse_js_file(source_dir / "learnsets.js")
    pokedex_data = parse_js_file(source_dir / "pokedex.js")
    
    # Type chart - structure is {type: {damageTaken: {target_type_or_condition: multiplier}}}
    type_chart = {}
    if type_chart_data:
        for outer_key, inner in type_chart_data.items():
            damage_taken = inner.get("damageTaken", {})
            # Only include entries that are type-based (keys are type names)
            # Skip non-type keys like prankster, par, brn, trapped, stellar
            for target_key, mult in damage_taken.items():
                if target_key == "stellar" or mult == 0:
                    continue
                # Check if target_key is a valid type (alphanumeric only)
                if re.match(r"^[a-zA-Z]+$", target_key):
                    type_chart[outer_key.lower()] = {target_key.lower(): mult}
    
    with open(out_dir / "type_chart.json", "w") as f:
        json.dump(type_chart, f)
    
    # Natures - hardcoded 25 natures
    natures = {
        "hardy": {"boosted": None, "reduced": None},
        "docile": {"boosted": "atk", "reduced": "def"},
        "serious": {"boosted": "spa", "reduced": "spe"},
        "bashful": {"boosted": "spd", "reduced": "atk"},
        "quirky": {"boosted": "def", "reduced": "spe"},
        "hasty": {"boosted": "spd", "reduced": "atm"},
        "adamant": {"boosted": "apa", "reduced": "spd"},
        "impish": {"boosted": "def", "reduced": "spa"},
        "lonely": {"boosted": "atm", "reduced": "spa"},
        "naive": {"boosted": "spe", "reduced": "atm"},
        "bold": {"boosted": "spd", "reduced": "apa"},
        "careful": {"boosted": "def", "reduced": "apa"},
        "honeyed": {"boosted": "spa", "reduced": "apa"},
        "naughty": {"boosted": "atm", "reduced": "spd"},
        "timid": {"boosted": "spe", "reduced": "apa"},
        "quiet": {"boosted": "apa", "reduced": "spa"},
        "mild": {"boosted": "apa", "reduced": "atm"},
        "relaxed": {"boosted": "atp", "reduced": "spd"},
        "rash": {"boosted": "apa", "reduced": "spd"},
        "sassy": {"boosted": "spa", "reduced": "atp"},
        "gentle": {"boosted": "spd", "reduced": "apa"},
        "jolly": {"boosted": "spe", "reduced": "spa"},
        "wimpish": {"boosted": "def", "reduced": "atp"},
    }
    
    with open(out_dir / "natures.json", "w") as f:
        json.dump(natures, f)
    
    # Items - filter by isNonstandard
    items = {}
    for name, entry in items_data.items():
        if not entry or entry.get("isNonstandard") in {"Past", "Unobtainable", "CAP", "LGPE"}:
            continue
        desc = entry.get("desc") or entry.get("shortDesc") or ""
        items[name.lower()] = {
            "name": name,
            "desc": desc,
            "gen": entry.get("generation", 1)
        }
    
    with open(out_dir / "items.json", "w") as f:
        json.dump(items, f)
    
    # Abilities - filter by isNonstandard
    abilities = {}
    for name, entry in abilities_data.items():
        if not entry or entry.get("isNonstandard") in {"Past", "Unobtainable", "CAP", "LGPE"}:
            continue
        desc = entry.get("desc") or entry.get("shortDesc") or ""
        abilities[name.lower()] = {
            "name": name,
            "desc": desc,
            "gen": entry.get("generation", 1)
        }
    
    with open(out_dir / "abilities.json", "w") as f:
        json.dump(abilities, f)
    
    # Moves - filter by isNonstandard
    moves = {}
    for name, entry in moves_data.items():
        if not entry or entry.get("isNonstandard") in {"Past", "Unobtainable", "CAP", "LGPE"}:
            continue
        acc = entry.get("accuracy")
        accuracy_val = True if acc is True else (100 if acc == 100 else None)
        desc = entry.get("desc") or entry.get("shortDesc") or ""
        moves[name.lower()] = {
            "name": name,
            "type": entry.get("type", "").lower(),
            "category": entry.get("category", "").lower(),
            "base_power": entry.get("basePower"),
            "accuracy": accuracy_val,
            "priority": entry.get("priority"),
            "pp": entry.get("pp"),
            "target": entry.get("target"),
            "flags": entry.get("flags") or {},
            "desc": desc
        }
    
    with open(out_dir / "moves.json", "w") as f:
        json.dump(moves, f)
    
    # Learnsets - only Gen 9 moves
    learnsets = {}
    for species_id, entry in learnsets_data.items():
        if not entry:
            continue
        gen9_moves = []
        for move_key, move_entry in entry.get("moves", {}).items():
            sources = move_entry.get("sources", [])
            if any(s.startswith("9") for s in sources):
                gen9_moves.append(move_key.lower())
        if gen9_moves:
            learnsets[normalize(species_id)] = sorted(gen9_moves)
    
    with open(out_dir / "learnsets.json", "w") as f:
        json.dump(learnsets, f)
    
    # Pokemon entries
    pokedex_entries = {}
    if pokedex_data:
        for num_entry in pokedex_data.get("BattlePokedex", {}).values():
            if not num_entry:
                continue
            species_id = num_entry.get("name") or num_entry.get("id")
            if not species_id:
                continue
            num_val = num_entry.get("num")
            species_num = num_val if num_val else None
            
            # Filter CAP, LGPE, Unobtainable
            is_nonstandard = num_entry.get("isNonstandard")
            if is_nonstandard in {"CAP", "LGPE", "Unobtainable"}:
                continue
            
            entry = {
                "name": species_id,
                "num": species_num,
                "types": [t.lower() for t in num_entry.get("types", [])],
                "base_stats": num_entry.get("baseStats"),
                "abilities": {},
                "tier": num_entry.get("tier"),
                "forme": num_entry.get("forme"),
                "base_species": num_entry.get("baseSpecies"),
                "learnset": []
            }
            
            # Abilities
            for ability_id in num_entry.get("abilities", []):
                ab = normalize(ability_id.replace(" ", ""))
                entry["abilities"][ab] = True
            
            # Learnset - check against moves.json for Gen 9
            if learnsets:
                try:
                    learnset_data = json.loads(json5.dumps(moves_data.get("BattleMoves", {})))
                except:
                    learnset_data = moves_data.get("BattleMoves", {})
                
                # Find which of this pokemon's moves are Gen 9
                for move_key, move_entry in num_entry.get("moveLearnset", {}).items():
                    sources = move_entry.get("sources", [])
                    if any(s.startswith("9") for s in sources):
                        entry["learnset"].append(move_key.lower())
            
            # Store as file
            with open(out_dir / "pokemon" / f"{species_num}.{normalize(species_id)}.json", "w") as f:
                json.dump(entry, f)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python query/etl.py raw knowledge")
        sys.exit(1)
    build(sys.argv[1], sys.argv[2])
