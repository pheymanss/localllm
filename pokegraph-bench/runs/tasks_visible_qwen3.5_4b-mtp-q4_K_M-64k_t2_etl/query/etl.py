#!/usr/bin/env python3
"""
ETL for Pokemon Showdown data: raw -> JSON outputs
"""

from pathlib import Path
import json
import json5
import os
import re
import subprocess
import sys


def normalize_id(s):
    """Normalize ID to lowercase alphanumeric only."""
    return re.sub(r"[^a-z0-9]", "", s.lower())


def extract_data(obj):
    """Extract data from JavaScript object literal. Returns the first key-value pair."""
    if not isinstance(obj, dict) or len(obj) != 1:
        return {}

    # The format is {BattleX: {...}} - return the inner value
    name = list(obj.keys())[0]
    return obj[name]


def load_js_file(filepath):
    """Load a JavaScript file containing exports.BattleX = {...}."""
    # Use Path to properly read the file
    p = Path(filepath)
    content = p.read_text().strip()

    # Find first { and last }
    first_brace = content.find('{')
    last_brace = content.rfind('}') + 1

    if first_brace == -1 or last_brace == -1:
        return None

    data_str = content[first_brace:last_brace]

    # Parse with json5 for unquoted keys
    parsed = json5.loads(data_str)
    return parsed


def transform_type_chart(source_dir):
    """Transform type chart data."""
    data = load_js_file(os.path.join(source_dir, "typechart.js"))
    battle_data = extract_data(data)

    # Map damageTaken values to multiplier
    value_map = {0: 1.0, 1: 2.0, 2: 0.5, 3: 0.0}

    type_chart = {}
    # The structure is {type_name: {damageTaken: {...}, HPivs: {}, HPdvs: {...}}}
    # Each type has a damageTaken dict where keys are attacking types and values are multipliers
    for type_name, type_info in battle_data.items():
        # Skip "Stellar" key and non-type keys (prankster, par, etc.)
        if type_name == "Stellar" or not type_name.isalpha() or type_name.lower() != type_name:
            continue

        attacking = type_info.get("damageTaken", {})
        multiplier = value_map.get(attacking, 1.0)

        # Only include if multiplier is not 1.0 (base case)
        if multiplier == 1.0:
            continue

        type_chart[type_name.lower()] = {attacking.lower(): multiplier}

    return type_chart


def transform_natures():
    """Return hardcoded natures."""
    # Five neutral natures: hardy, docile, serious, bashful, quirky
    natures = [
        ("hardy", {"boosted": None, "reduced": None}),
        ("docile", {"boosted": None, "reduced": None}),
        ("serious", {"boosted": None, "reduced": None}),
        ("bashful", {"boosted": None, "reduced": None}),
        ("quirky", {"boosted": None, "reduced": None}),
    ]

    stat_boosts = {
        "atk": 1, "def": 2, "spa": 3, "spd": 4, "spe": 5,
    }

    # Generate rest of natures based on stat boosts
    all_stats = list(stat_boosts.keys())

    for i in range(5, 25):
        s1 = all_stats[i % 5]
        s2 = all_stats[(i + 1) % 5]
        natures.append((f"{s1}s", {"boosted": stat_boosts[s1], "reduced": stat_boosts[s2]}))

    return {name: data for name, data in natures}


def transform_items(source_dir):
    """Transform items.json."""
    data = load_js_file(os.path.join(source_dir, "items.js"))
    battle_data = data

    result = {}
    forbidden = {"Past", "Unobtainable", "CAP", "LGPE"}

    for name, entry in battle_data.items():
        is_nonstandard = entry.get("isNonstandard")
        if is_nonstandard and is_nonstandard.lower() in [x.lower() for x in forbidden]:
            continue

        result[name] = {
            "name": entry.get("name"),
        }

        # Handle desc - try shortDesc first, then desc
        short_desc = entry.get("shortDesc") or entry.get("desc", "")
        if short_desc:
            result[name]["desc"] = short_desc

        gen = entry.get("gen")
        if gen is not None:
            result[name]["gen"] = gen

    return result


def transform_abilities(source_dir):
    """Transform abilities.json."""
    data = load_js_file(os.path.join(source_dir, "abilities.js"))
    battle_data = extract_data(data, "BattleAbilities")

    result = {}
    forbidden = {"Past", "Unobtainable", "CAP", "LGPE"}

    for name, entry in battle_data.items():
        is_nonstandard = entry.get("isNonstandard")
        if is_nonstandard and is_nonstandard.lower() in [x.lower() for x in forbidden]:
            continue

        result[name] = {
            "name": entry.get("name"),
        }

        short_desc = entry.get("shortDesc") or entry.get("desc", "")
        if short_desc:
            result[name]["desc"] = short_desc

        gen = entry.get("gen")
        if gen is not None:
            result[name]["gen"] = gen

    return result


def transform_moves(source_dir):
    """Transform moves.json."""
    data = load_js_file(os.path.join(source_dir, "moves.js"))
    battle_data = extract_data(data, "BattleMovedex")

    # Map for true accuracy (never misses)
    truthy_accuracy = {"true", True}

    result = {}
    forbidden = {"Past", "Unobtainable", "CAP", "LGPE"}

    for name, entry in battle_data.items():
        is_nonstandard = entry.get("isNonstandard")
        if is_nonstandard and is_nonstandard.lower() in [x.lower() for x in forbidden]:
            continue

        result[name] = {
            "type": entry.get("type", "").lower(),
            "category": entry.get("category", "").lower(),
            "base_power": entry.get("basePower"),
        }

        # Accuracy - can be true (never misses), 100, or a number
        accuracy = entry.get("accuracy")
        if accuracy is True or accuracy == "true" or accuracy == 100:
            result[name]["accuracy"] = True
        elif isinstance(accuracy, int):
            result[name]["accuracy"] = accuracy
        else:
            # If it's a string that looks like a number
            try:
                result[name]["accuracy"] = int(accuracy)
            except (ValueError, TypeError):
                result[name]["accuracy"] = accuracy

        result[name]["base_power"] = entry.get("basePower")
        result[name]["priority"] = entry.get("priority", 0)
        result[name]["pp"] = entry.get("pp", 15)
        result[name]["target"] = entry.get("target", "normal")

        # flags is a dictionary like {"contact":1,"punch":1}
        flags = entry.get("flags", {})
        if flags:
            result[name]["flags"] = {str(k): v for k, v in flags.items()}
        else:
            result[name]["flags"] = {}

        # desc (shortDesc)
        short_desc = entry.get("shortDesc") or entry.get("desc", "")
        if short_desc:
            result[name]["desc"] = short_desc

    return result


def transform_learnsets(source_dir):
    """Transform learnsets.json - keep only moves with Gen 9 sources."""
    data = load_js_file(os.path.join(source_dir, "learnsets.js"))
    battle_data = extract_data(data, "BattleLearnsets")

    # Build reverse map: source -> generation
    gen_map = {
        "L": 1, "E": 2, "M": 3, "T": 4, "V": 5,
        "6L": 6, "7L": 7, "8L": 8, "9L": 9,
        "6E": 6, "7E": 7, "8E": 8, "9E": 9,
        "6M": 6, "7M": 7, "8M": 8, "9M": 9,
        "6T": 6, "7T": 7, "8T": 8, "9T": 9,
        "6S": 6, "7S": 7, "8S": 8, "9S": 9,
        "3L": 3, "4L": 4, "5L": 5, "6L": 6, "7L": 7, "8L": 8, "9L": 9,
        "3E": 3, "4E": 4, "5E": 5, "6E": 6, "7E": 7, "8E": 8, "9E": 9,
        "3M": 3, "4M": 4, "5M": 5, "6M": 6, "7M": 7, "8M": 8, "9M": 9,
        "3T": 3, "4T": 4, "5T": 5, "6T": 6, "7T": 7, "8T": 8, "9T": 9,
        "3S": 3, "4S": 4, "5S": 5, "6S": 6, "7S": 7, "8S": 8, "9S": 9,
        "V": 5,
    }

    def has_gen_9(learnset):
        """Check if any source string starts with '9'."""
        for source in learnset:
            if isinstance(source, str) and source.startswith("9"):
                return True
        return False

    result = {}
    for name, entry in battle_data.items():
        # Skip missingno - has no forms/abilities info
        if name == "missingno" or not isinstance(entry.get("learnset"), dict):
            continue

        if not has_gen_9(entry["learnset"]):
            continue

        result[name] = sorted(entry["learnset"])

    return result


def transform_pokemon(source_dir, out_dir):
    """Transform pokemon/<id>.json files."""
    data = load_js_file(os.path.join(source_dir, "pokedex.js"))
    battle_data = extract_data(data, "BattlePokedex")

    # Build reverse map for normalization
    def reverse_normalize(species_id):
        return normalize_id(species_id)

    result = {}
    forbidden = {"Past", "Unobtainable", "CAP", "LGPE"}

    for name, entry in battle_data.items():
        # Skip CAP and LGPE entries
        is_nonstandard = entry.get("isNonstandard")
        if is_nonstandard and is_nonstandard.lower() in [x.lower() for x in forbidden]:
            continue

        types = entry.get("types", [])
        if not isinstance(types, list):
            continue

        # Get num
        num = entry.get("num")
        if num is None:
            name = normalize_id(name)

        base_stats = {
            k + "": v for k, v in entry.get("baseStats", {}).items()
        }
        # Convert int to string for stats like Spe that might have issues
        for key in base_stats:
            if isinstance(base_stats[key], int):
                base_stats[key] = str(base_stats[key])

        abilities_str = ",".join(entry.get("abilities", {}).keys())
        abilities = {}
        for slot in entry.get("abilities", {}):
            abilities[slot] = normalize_id(slot.replace("-", ""))

        forms = []
        prevo = entry.get("prevo") or entry.get("prevo1") or entry.get("prevo2") or entry.get("prevo3")
        if prevo:
            forms.append(prevo)

        # Handle otherFormes if not using forms
        if "forme" in entry:
            forms = [entry["forme"]]

        result[name] = {
            "types": types,
            "base_stats": base_stats,
            "abilities": abilities,
            "tier": entry.get("tier"),
            "forms": forms or None,
            "prevo": prevo or None,
        }

    return result


def main():
    if len(sys.argv) < 3:
        print("Usage: python query/etl.py <source_dir> <out_dir>", file=sys.stderr)
        sys.exit(1)

    source_dir = sys.argv[1]
    out_dir = sys.argv[2]

    # Create output directories
    os.makedirs(os.path.join(out_dir, "pokemon"), exist_ok=True)

    # Transform type chart
    type_chart = transform_type_chart(source_dir)
    with open(os.path.join(out_dir, "type_chart.json"), "w") as f:
        json.dump(type_chart, f)

    # Transform natures (hardcoded)
    natures = transform_natures()
    with open(os.path.join(out_dir, "natures.json"), "w") as f:
        json.dump(natures, f)

    # Transform items
    items = transform_items(source_dir)
    with open(os.path.join(out_dir, "items.json"), "w") as f:
        json.dump(items, f)

    # Transform abilities
    abilities = transform_abilities(source_dir)
    with open(os.path.join(out_dir, "abilities.json"), "w") as f:
        json.dump(abilities, f)

    # Transform moves
    moves = transform_moves(source_dir)
    with open(os.path.join(out_dir, "moves.json"), "w") as f:
        json.dump(moves, f)

    # Transform learnsets
    learnsets = transform_learnsets(source_dir)
    with open(os.path.join(out_dir, "learnsets.json"), "w") as f:
        json.dump(learnsets, f)

    # Transform pokemon
    pokemon = transform_pokemon(source_dir, out_dir)
    for name, entry in pokemon.items():
        filename = f"{normalize_id(name)}.json"
        with open(os.path.join(out_dir, "pokemon", filename), "w") as f:
            json.dump(pokemon[name], f)


if __name__ == "__main__":
    main()
