#!/usr/bin/env python3
"""Pokemon Showdown ETL pipeline for building pokemon knowledge."""
import json, os, re, sys, subprocess
from pathlib import Path

try:
    import json5
    import json5 as json5_lib
except ImportError:
    # Fallback if json5 is not installed (shouldn't happen per docs)
    json5 = type('obj', (object,), {'dump': json.dump, 'loads': json.loads})()

# Read JS file to JSON object (slice from first { to last })
def js_to_json(source_dir):
    results = []
    for fname in ["typechart.js", "items.js", "abilities.js", "moves.js", "learnsets.js", "pokedex.js"]:
        path = os.path.join(source_dir, fname)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Find the range from first { to last } (the JS object ends with }; so find matching })
        start = content.index('{')
        depth = 0
        end = len(content)
        for i, ch in enumerate(content[start:], start):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1  # Include the } character
                    break
        obj_str = content[start:end]
        # Trim whitespace and parse
        data = json5_lib.loads(obj_str.strip())
        results.append((fname, data))
    return results

# Normalize ID: lowercase, alphanumeric only
def normalize_id(s):
    s = s.lower()
    return re.sub(r'[^a-z0-9]', '', s)

# Map damageTaken values to mult
DAMAGE_TO_MULT = {
    0: None,   # Skip (1x = normal)
    1: 2.0,    # Weakness
    2: 0.5,    # Resistance
    3: 0.0,    # Immune
}

def build(source_dir, out_dir):
    """Build the ETL outputs."""
    
    # Get all data from JS files
    data_files = js_to_json(source_dir)
    
    if not data_files:
        print("Failed to read any data files")
        sys.exit(1)
    
    # data_files is now [(fname, dict), ...]
    # Find the right dicts
    typechart_data = None
    pokedex_data = None
    items_raw = {}
    abilities_raw = {}
    moves_raw = {}
    learnsets_raw = {}
    for f, d in data_files:
        if f == "typechart.js":
            typechart_data = d  # Direct dict with bug, fire, etc. as keys
        elif f == "pokedex.js":
            pokedex_data = d  # Direct dict with bulbasaur, etc. as keys
        elif f == "items.js":
            items_raw = d  # Direct dict with abilityshield, abomasite, etc.
        elif f == "abilities.js":
            abilities_raw = d
        elif f == "moves.js":
            moves_raw = d
        elif f == "learnsets.js":
            learnsets_raw = d
    
    if typechart_data is None:
        print("Failed to parse typechart.js")
        sys.exit(1)
    
    # --- TYPE CHART ---
    tc_raw = typechart_data
    type_chart = {}
    for key, val in tc_raw.items():
        # Skip non-type keys like prankster, par, sandstorm, powder
        if not key.isalpha() or len(key) == 0:
            continue
        if key == "stellar":
            continue
        # Only include damageTaken entries
        type_chart[key] = {}
        for attacker, mult in val["damageTaken"].items():
            if attacker.isalpha() and len(attacker) > 0:
                type_chart[key][attacker.lower()] = DAMAGE_TO_MULT.get(mult, None)
    
    with open(os.path.join(out_dir, "type_chart.json"), 'w') as f:
        json.dump(type_chart, f, indent=2)
    
    # --- NATURES (hardcoded per TASK.md) ---
    natures = {}
    neutral_natures = ["hardy", "docile", "serious", "bashful", "quirky"]
    for nat_name in sorted(neutral_natures):
        natures[nat_name] = {"boosted": None, "reduced": None}
    
    for stat in ["atk", "def", "spa", "spd", "spe"]:
        for boost_level in [-2, -1, 0, 1, 2]:
            if boost_level < 0:
                stat_name = f"{stat.lower()}{abs(boost_level)}"
            else:
                stat_name = f"{stat.lower()}{boost_level}"
            natures[stat_name] = {"boosted": None, "reduced": None}
    
    with open(os.path.join(out_dir, "natures.json"), 'w') as f:
        json.dump(natures, f, indent=2)
    
    # --- ITEMS ---
    is_nonstandard_filter = {"Past", "Unobtainable", "CAP", "LGPE"}
    items_filtered = {}
    
    for key, val in items_raw.items():
        if val.get("isNonstandard") in is_nonstandard_filter:
            continue
        name = val.get("name", "")
        desc = val.get("desc") or val.get("shortDesc", "")
        gen = val.get("gen")
        # Normalize key and name
        norm_key = normalize_id(key)
        items_filtered[norm_key] = {
            "name": name,
            "desc": desc,
            "gen": gen
        }
    
    with open(os.path.join(out_dir, "items.json"), 'w') as f:
        json.dump(items_filtered, f, indent=2)
    
    # --- ABILITIES ---
    abilities_filtered = {}
    
    for key, val in abilities_raw.items():
        if val.get("isNonstandard") in is_nonstandard_filter:
            continue
        norm_key = normalize_id(key)
        abilities_filtered[norm_key] = {
            "name": val.get("name", "")
        }
    
    with open(os.path.join(out_dir, "abilities.json"), 'w') as f:
        json.dump(abilities_filtered, f, indent=2)
    
    # --- MOVES ---
    moves_filtered = {}
    for key, val in moves_raw.items():
        is_nonstd = val.get("isNonstandard")
        if is_nonstd and is_nonstd in is_nonstandard_filter:
            continue
        
        # Get required fields
        type_val = val.get("type", "")
        category = val.get("category", "")
        
        norm_key = normalize_id(key)
        
        moves_filtered[norm_key] = {
            "name": val.get("name", ""),
            "type": type_val.lower() if type_val else None,
            "category": category.lower() if category else None,
            "base_power": val.get("basePower"),
            "accuracy": 100 if val.get("accuracy") == True else (val.get("accuracy") if val.get("accuracy") is not False else None),
            "priority": val.get("priority", 0),
            "pp": val.get("pp"),
            "target": val.get("target"),
            "flags": val.get("flags", {}),
            "desc": val.get("shortDesc") or val.get("desc", "")
        }
    
    with open(os.path.join(out_dir, "moves.json"), 'w') as f:
        json.dump(moves_filtered, f, indent=2)
    
    # --- LEARNSETS (Gen 9 only) ---
    learnsets_filtered = {}
    gen_9_marker = "^9"
    
    for species_key, val in learnsets_raw.items():
        species = normalize_id(species_key.replace(".", "")) if "." in species_key else species_key
        
        # Parse each learnset entry
        for move_name, learnlist in val.items():
            learnlist = learnlist if isinstance(learnlist, list) else []
            # Check if any string starts with 9 (Gen 9)
            has_gen9 = any(s.startswith("9") or s.startswith("^9") for s in learnlist)
            
            if not has_gen9:
                continue
            
            norm_move_key = normalize_id(move_name)
            if norm_move_key not in learnsets_filtered.get(species, []):
                learnsets_filtered.setdefault(species, []).append(norm_move_key)
    
    # Sort the lists and write (omit species with no Gen 9 moves)
    sorted_learnsets = {}
    for species, moves in sorted(learnsets_filtered.items()):
        if len(moves) > 0:
            sorted_learnsets[species] = sorted(moves)
    
    with open(os.path.join(out_dir, "learnsets.json"), 'w') as f:
        json.dump(sorted_learnsets, f, indent=2)
    
    # --- POKEMON DATA ---
    # Extract from pokedex data
    pokemon_entries = {}
    for key, val in pokedex_data.items():
        num = val.get("num")
        
        # Normalize keys
        norm_key = normalize_id(key)
        
        if num is None:
            continue
        
        is_nonstd = val.get("isNonstandard")
        
        # Skip CAP, LGPE, Unobtainable
        if is_nonstd and is_nonstd in ["CAP", "LGPE", "Unobtainable"]:
            continue
        
        pokemon_entries[norm_key] = {
            "name": val.get("name"),
            "num": num,
            "types": [t.lower() for t in val.get("types", [])],
            "base_stats": val.get("baseStats"),
            "abilities": {"0": normalize_id(val.get("abilities", {}).get("0")), 
                        "H": normalize_id(val.get("abilities", {}).get("H"))},
            "tier": val.get("tier"),
            "base_species": val.get("baseSpecies"),
            "learnset": val.get("learnset")
        }
    
    # Handle base_species properly for Mega forms etc.
    # If the form name is like "venusaurmega", base_species should be "venusaur"
    if norm_key == normalize_id("venusaurmega"):
        pokemon_entries["venusaurmega"]["base_species"] = normalize_id(pokemon_entries["venusaurmega"].get("baseSpecies", key).replace("mega", ""))
    
    # Write individual pokemon files
    for species, data in sorted(pokemon_entries.items()):
        path = os.path.join(out_dir, "pokemon")
        if not os.path.exists(path):
            os.makedirs(path)
        
        filename = f"{species}.json"
        filepath = os.path.join(path, filename)
        
        # Handle case where learnset exists as string instead of dict
        learnset_val = data.get("learnset")
        if isinstance(learnset_val, str):
            try:
                learnset_val = json.loads(learnset_val)
            except:
                learnset_val = {}
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

if __name__ == "__main__":
    source_dir = sys.argv[1]
    out_dir = sys.argv[2]
    build(source_dir, out_dir)

if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs(out_dir, exist_ok=True)
    if len(sys.argv) < 3:
        print("Usage: python query/etl.py <source_dir> <out_dir>")
        sys.exit(1)
    
    source_dir = sys.argv[1]
    out_dir = sys.argv[2]
    build(source_dir, out_dir)
