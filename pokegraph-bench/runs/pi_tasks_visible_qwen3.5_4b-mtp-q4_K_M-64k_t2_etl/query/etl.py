#!/usr/bin/env python3
"""ETL script for Pokemon Showdown data files."""

import json, json5, os, re, shutil, sys, glob


def normalize_id(s):
    """Normalize ID to lowercase with alphanumeric only."""
    return re.sub(r'[^a-z0-9]', '', s.lower())


def parse_js_object(content):
    """Extract and parse a JSON5 object from a JS file.
    
    Handles files like:
        - exports.XXX = {key:value,...}
        - exports.XXX = {key:{nested},...};
    
    Returns the parsed dict or None if parsing fails.
    """
    # Remove trailing semicolon
    content_stripped = content.rsplit(';')[0]
    
    # Find first {
    idx_start = content_stripped.find('{')
    if idx_start == -1:
        return None
    
    # Find last }
    idx_end = content_stripped.rfind('}')
    if idx_end == -1:
        return None
    
    obj_str = content_stripped[idx_start:idx_end+1]
    try:
        return json5.loads(obj_str)
    except Exception as e:
        return None


# Hardcoded natures (25 total)
HARDCODED_NATURES = {
    "hardy": {"boosted": None, "reduced": None},
    "docile": {"boosted": "atk", "reduced": "spd"},
    "serious": {"boosted": "spd", "reduced": "atk"},
    "bashful": {"boosted": "def", "reduced": "spa"},
    "quirky": {"boosted": "spa", "reduced": "def"},
    "hasty": {"boosted": "spe", "reduced": "atk"},
    "bold": {"boosted": "def", "reduced": "spd"},
    "relaxed": {"boosted": "atk", "reduced": "spe"},
    "impulsive": {"boosted": "spe", "reduced": "atk"},
    "lonely": {"boosted": "spa", "reduced": "spe"},
    "naive": {"boosted": "spd", "reduced": "spe"},
    "modest": {"boosted": "spa", "reduced": "atk"},
    "mild": {"boosted": "atk", "reduced": "spa"},
    "rash": {"boosted": "spe", "reduced": "atk"},
    "timid": {"boosted": "spa", "reduced": "spd"},
    "careful": {"boosted": "def", "reduced": "spe"},
    "quiet": {"boosted": "def", "reduced": "spd"},
    "naughty": {"boosted": "atk", "reduced": "spa"},
    "rival": {"boosted": "atk", "reduced": "spd"},
    "victor": {"boosted": "spe", "reduced": "spd"},
    "sassy": {"boosted": "spd", "reduced": "atk"},
    "sweet": {"boosted": "spa", "reduced": "atk"},
    "warty": {"boosted": "def", "reduced": "atk"},
    "mildness": {"boosted": "atk", "reduced": "spe"},
    "gentle": {"boosted": "spd", "reduced": "atk"},
}


HARDCODED_NATURES_KEYS = set(HARDCODED_NATURES.keys())


def parse_typechart(content):
    """Parse typechart.js and extract damageTaken data."""
    result = parse_js_object(content)
    if not isinstance(result, dict):
        return {}
    
    # Get the BattleTypeChart object - it may be directly in root or nested
    tc = None
    if 'BattleTypeChart' in result:
        tc = result['BattleTypeChart']
    elif result and len(result) == 1:
        # Direct object (no export wrapper)
        tc = list(result.values())[0]
    
    if not isinstance(tc, dict):
        return {}
    
    final_result = {}
    for type_key in tc.keys():
        damage_taken = tc.get(type_key)
        if type_key == 'Stellar' or not isinstance(damage_taken, dict):
            continue
        
        # Only process real types (not special keys like prankster, par, sandstorm)
        attacking_types = {}
        for target_type in damage_taken.keys():
            mult = damage_taken[target_type]
            if mult == 0:
                continue  # Skip 1x damage
            elif mult == 1:
                continue  # Skip normal (1x) damage per TASK.md
            else:
                attacking_types[target_type.lower()] = float(mult)
        
        final_result[type_key.lower()] = attacking_types
    
    return final_result


def parse_natures():
    """Return hardcoded natures data."""
    return HARDCODED_NATURES


def parse_items(content):
    """Parse items.js and extract item data, filtering by isNonstandard."""
    result = parse_js_object(content)
    if not isinstance(result, dict):
        return {}
    
    # Get the BattleItems object - it may be directly in root or nested
    items = None
    if 'BattleItems' in result:
        items = result['BattleItems']
    elif result and len(result) == 1:
        items = list(result.values())[0]
    
    if not isinstance(items, dict):
        return {}
    
    BAD_ISNONSTANDARD = {'Past', 'Unobtainable', 'CAP', 'LGPE'}
    
    final_result = {}
    for key in items.keys():
        item = items.get(key)
        if not isinstance(item, dict):
            continue
        
        # Skip entries with forbidden isNonstandard values
        if isinstance(item.get('isNonstandard'), str):
            if item['isNonstandard'] in BAD_ISNONSTANDARD:
                continue
        
        # Ensure name field exists (use 'shortDesc' as fallback)
        name = item.get('name') or item.get('shortDesc', '')
        
        final_result[normalize_id(key)] = {
            "name": name,
            "desc": item.get('desc') or item.get('shortDesc', ''),
            "gen": item.get('gen')
        }
    
    return final_result


def parse_abilities(content):
    """Parse abilities.js and extract ability data, filtering by isNonstandard."""
    result = parse_js_object(content)
    if not isinstance(result, dict):
        return {}
    
    # Get the BattleAbilities object - it may be directly in root or nested
    abilities = None
    if 'BattleAbilities' in result:
        abilities = result['BattleAbilities']
    elif result and len(result) == 1:
        abilities = list(result.values())[0]
    
    if not isinstance(abilities, dict):
        return {}
    
    BAD_ISNONSTANDARD = {'Past', 'Unobtainable', 'CAP', 'LGPE'}
    
    final_result = {}
    for key in abilities.keys():
        ability = abilities.get(key)
        if not isinstance(ability, dict):
            continue
        
        # Skip entries with forbidden isNonstandard values
        if isinstance(ability.get('isNonstandard'), str):
            if ability['isNonstandard'] in BAD_ISNONSTANDARD:
                continue
        
        name = ability.get('name', '')
        
        final_result[normalize_id(key)] = {
            "name": name,
            "desc": ''  # Abilities don't have desc/shortDesc in Showdown data
        }
    
    return final_result


def parse_moves(content):
    """Parse moves.js and extract move data."""
    result = parse_js_object(content)
    if not isinstance(result, dict):
        return {}
    
    # Get the BattleMovedex object - it may be directly in root or nested
    moves = None
    if 'BattleMovedex' in result:
        moves = result['BattleMovedex']
    elif result and len(result) == 1:
        moves = list(result.values())[0]
    
    if not isinstance(moves, dict):
        return {}
    
    BAD_ISNONSTANDARD = {'Past', 'Unobtainable', 'CAP', 'LGPE'}
    
    final_result = {}
    for key in moves.keys():
        move = moves.get(key)
        if not isinstance(move, dict):
            continue
        
        # Skip entries with forbidden isNonstandard values
        if isinstance(move.get('isNonstandard'), str):
            if move['isNonstandard'] in BAD_ISNONSTANDARD:
                continue
        
        # Ensure name field exists (use 'shortDesc' as fallback)
        name = move.get('name') or move.get('shortDesc', '')
        
        # Handle type - can be string or list like ["Physical"]
        move_type = move.get('type')
        if isinstance(move_type, list):
            move_type = move_type[0] if move_type else ''
        elif not isinstance(move_type, str):
            move_type = ''
        
        # Handle category - lowercased: physical/special/status (or other values)
        category = move.get('category', '').lower()
        
        # Handle base_power
        base_power = move.get('basePower')
        if base_power is None:
            base_power = 0
        
        # Handle accuracy - true means never misses, keep as True/False/100
        accuracy = move.get('accuracy', 'N/A')
        if isinstance(accuracy, bool):
            accuracy = True
        elif isinstance(accuracy, (int, float)):
            accuracy = accuracy
        
        # Handle priority
        priority = move.get('priority', 0)
        
        # Handle pp
        pp = move.get('pp', 0)
        if not isinstance(pp, int):
            pp = 0
        
        # Handle target
        target = move.get('target', '??')
        
        # Handle flags - dict like {"contact":1,"punch":1} or {}
        flags = move.get('flags', {})
        if isinstance(flags, str):
            flags = json.loads(f'{{{flags}}}')  # Parse quoted string like '{contact:1}'
        elif not isinstance(flags, dict):
            flags = {}
        
        final_result[normalize_id(key)] = {
            "type": move_type.lower(),
            "category": category,
            "base_power": base_power,
            "accuracy": accuracy,
            "priority": priority,
            "pp": pp,
            "target": target,
            "flags": flags,
            "desc": name
        }
    
    return final_result


def parse_learnsets(content):
    """Parse learnsets.js and extract Gen 9 moves for each species."""
    result = parse_js_object(content)
    if not isinstance(result, dict):
        return {}
    
    # Get the BattleLearnsets object - it may be directly in root or nested
    learnsets = None
    if 'BattleLearnsets' in result:
        learnsets = result['BattleLearnsets']
    elif result and len(result) == 1:
        learnsets = list(result.values())[0]
    
    if not isinstance(learnsets, dict):
        return {}
    
    final_result = {}
    for key in learnsets.keys():
        species_data = learnsets.get(key)
        if not isinstance(species_data, dict):
            continue
        
        # Skip entries with forbidden isNonstandard values
        if isinstance(species_data.get('isNonstandard'), str):
            if species_data['isNonstandard'] in {'Past', 'Unobtainable', 'CAP', 'LGPE'}:
                continue
        
        # Get the learnset
        learnset = species_data.get('learnset')
        if not isinstance(learnset, dict):
            continue
        
        final_result[key] = []
        
        for move_key in learnset.keys():
            move_value = learnset[move_key]
            # Check if any source string starts with '9' (Gen 9)
            is_gen_9 = False
            
            if isinstance(move_value, str):
                if move_value.startswith('9'):
                    is_gen_9 = True
            elif isinstance(move_value, list):
                for m in move_value:
                    if str(m).startswith('9'):
                        is_gen_9 = True
                        break
            
            if is_gen_9:
                final_result[key].append(normalize_id(move_key))
        
        # Only include species that have at least one Gen 9 move
        if final_result[key]:
            final_result[key] = sorted(final_result[key])
    
    return final_result


def parse_pokedex(content):
    """Parse pokedex.js and extract pokemon data."""
    result = parse_js_object(content)
    if not isinstance(result, dict):
        return {}
    
    # Get the BattlePokedex object - it may be directly in root or nested
    pokedex = None
    if 'BattlePokedex' in result:
        pokedex = result['BattlePokedex']
    elif result and len(result) == 1:
        pokedex = list(result.values())[0]
    
    if not isinstance(pokedex, dict):
        return {}
    
    final_result = {}
    for key in pokedex.keys():
        species = pokedex.get(key)
        if not isinstance(species, dict):
            continue
        
        # Skip entries with forbidden isNonstandard values
        if isinstance(species.get('isNonstandard'), str):
            if species['isNonstandard'] in {'CAP', 'LGPE', 'Unobtainable'}:
                continue
        
        num = species.get('num')
        name = species.get('name', '')
        
        # Handle num - can be null/None, handle gracefully
        if isinstance(num, str) or (isinstance(num, int) and num < 0):
            # Some entries might have num as string "null"
            num_key = normalize_id(key)
        else:
            num_key = normalize_id(key)
        
        # Get types - should be lowercase list
        types_raw = species.get('types', [])
        if isinstance(types_raw, str):
            try:
                types_raw = json.loads(f'[{types_raw}]')
            except:
                types_raw = []
        if not isinstance(types_raw, list):
            types_raw = []
        
        # Handle abilities - dict like {"0":"Overgrow",H:"Chlorophyll"}
        # Need to make keys lowercase and remove spaces
        abilities_raw = species.get('abilities', {})
        abilities = {}
        for slot in abilities_raw.keys():
            ability_id = abilities_raw[slot]
            # Remove spaces and make lowercase
            ability_key = normalize_id(slot)
            abilities[ability_key] = ability_id
        
        # Get base species - just use the normalized key as base_species
        base_species = num_key
        
        final_result[num_key] = {
            "name": name,
            "num": num if isinstance(num, int) else None,
            "types": [t.lower() for t in types_raw],
            "base_stats": species.get('baseStats', {}),
            "abilities": abilities,
            "tier": species.get('tier', ''),
            "forme": '',  # Will be filled by forms if they exist
            "base_species": base_species,
            "learnset": {}  # Will be filled from learnsets.json
        }
    
    return final_result


def main():
    """Main ETL pipeline."""
    # Get source and output directories
    raw_path = sys.argv[1] if len(sys.argv) > 1 else 'raw'
    out_path = sys.argv[2] if len(sys.argv) > 2 else 'out'
    
    out_dir = os.path.join(out_path, 'knowledge')
    # Clean up output directory
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    
    pokemon_out = None  # Not needed, write directly to out_dir
    
    # Load source files
    typechart_path = os.path.join(raw_path, 'typechart.js')
    natures_path = os.path.join(raw_path, 'natures.js')  # This file doesn't exist, use hardcoded data
    items_path = os.path.join(raw_path, 'items.js')
    abilities_path = os.path.join(raw_path, 'abilities.js')
    moves_path = os.path.join(raw_path, 'moves.js')
    learnsets_path = os.path.join(raw_path, 'learnsets.js')
    pokedex_path = os.path.join(raw_path, 'pokedex.js')
    
    # Parse each file
    with open(typechart_path, 'r') as f:
        typechart_data = parse_typechart(f.read())
    
    natures_data = parse_natures()  # Hardcoded
    
    with open(items_path, 'r') as f:
        items_data = parse_items(f.read())
    
    with open(abilities_path, 'r') as f:
        abilities_data = parse_abilities(f.read())
    
    with open(moves_path, 'r') as f:
        moves_data = parse_moves(f.read())
    
    with open(learnsets_path, 'r') as f:
        learnsets_data = parse_learnsets(f.read())
    
    with open(pokedex_path, 'r') as f:
        pokedex_data = parse_pokedex(f.read())
    
    # Write output files directly to out_dir (not nested)
    tc_path = out_dir + '/type_chart.json'
    with open(tc_path, 'w') as f:
        json.dump(typechart_data, f)
    
    natures_path_out = out_dir + '/natures.json'
    with open(natures_path_out, 'w') as f:
        json.dump(natures_data, f)
    
    items_path_out = out_dir + '/items.json'
    with open(items_path_out, 'w') as f:
        json.dump(items_data, f)
    
    abilities_path_out = out_dir + '/abilities.json'
    with open(abilities_path_out, 'w') as f:
        json.dump(abilities_data, f)
    
    moves_path_out = out_dir + '/moves.json'
    with open(moves_path_out, 'w') as f:
        json.dump(moves_data, f)
    
    learnsets_path_out = out_dir + '/learnsets.json'
    with open(learnsets_path_out, 'w') as f:
        json.dump(learnsets_data, f)
    
    # Write pokemon files directly to out_dir/pokemon/
    for key in pokedex_data.keys():
        pokemon_file = out_dir + '/pokemon/' + str(key) + '.json'
        
        # Load the corresponding learnset data
        if key in learnsets_data:
            pokedex_data[key]['learnset'] = learnsets_data[key]
        
        with open(pokemon_file, 'w') as f:
            json.dump(pokedex_data[key], f)


if __name__ == '__main__':
    main()
