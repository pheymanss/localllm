import json, os, re, sys

def slice_object(src, dst):
    i = src.index('{')
    j = src.rindex('}')
    return json.loads(src[i:j+1])

def clean_id(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())

def read_file(path):
    with open(path, 'r', errors='replace') as f:
        return f.read()

def build(source_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.join(out_dir, 'pokemon'), exist_ok=True)

    raw = read_file(read_file(os.path.join(source_dir, 'typechart.js')))
    tc = slice_object(raw, raw)
    type_chart = {}
    for d, moves in tc['damageTaken'].items():
        if d == 'stellar':
            continue
        for a, mult in moves.items():
            if a == 'stellar':
                continue
            type_chart[d.lower()][a.lower()] = float(mult)
    with open(os.path.join(out_dir, 'type_chart.json'), 'w') as f:
        json.dump(type_chart, f)

    natures = {}
    for name, boosts in tc['natures'].items():
        natures[name] = {'boosted': boosts[0], 'reduced': boosts[1]}
    with open(os.path.join(out_dir, 'natures.json'), 'w') as f:
        json.dump(natures, f)

    def filter_entries(entries):
        result = []
        for e in entries.values():
            if e.get('isNonstandard', '') in ('Past', 'Unobtainable', 'CAP', 'LGPE'):
                continue
            result.append(e)
        return result

    items = filter_entries(slice_object(read_file(read_file(os.path.join(source_dir, 'items.js'))), read_file(read_file(os.path.join(source_dir, 'items.js')))))
    with open(os.path.join(out_dir, 'items.json'), 'w') as f:
        json.dump([{k: e.get(k) for k in ('name', 'desc', 'gen')} for e in items], f)

    abilities = filter_entries(slice_object(read_file(read_file(os.path.join(source_dir, 'abilities.js'))), read_file(read_file(os.path.join(source_dir, 'abilities.js')))))
    with open(os.path.join(out_dir, 'abilities.json'), 'w') as f:
        json.dump([{k: e.get(k) for k in ('name', 'desc', 'gen')} for e in abilities], f)

    moves = filter_entries(slice_object(read_file(read_file(os.path.join(source_dir, 'moves.js'))), read_file(read_file(os.path.join(source_dir, 'moves.js')))))
    with open(os.path.join(out_dir, 'moves.json'), 'w') as f:
        json.dump([{k: e.get(k) for k in ('name', 'type', 'category', 'base_power', 'accuracy', 'priority', 'pp', 'target', 'flags', 'desc')} for e in moves], f)

    learnsets = slice_object(read_file(read_file(os.path.join(source_dir, 'learnsets.js'))), read_file(read_file(os.path.join(source_dir, 'learnsets.js'))))
    gen9_learnsets = {}
    for species, moves_list in learnsets.items():
        if any(str(m).startswith('9') for m in moves_list):
            gen9_learnsets[species] = sorted([str(m) for m in moves_list])
    with open(os.path.join(out_dir, 'learnsets.json'), 'w') as f:
        json.dump(gen9_learnsets, f)

    pokedex = slice_object(read_file(read_file(os.path.join(source_dir, 'pokedex.js'))), read_file(read_file(os.path.join(source_dir, 'pokedex.js'))))
    for name, e in pokedex.items():
        if e.get('isNonstandard', '') in ('CAP', 'LGPE', 'Unobtainable'):
            continue
        num = e.get('num') or ''
        pid = clean_id(num)
        types = [t.lower() for t in e.get('types', [])]
        abilities_ids = []
        for slot, aid in sorted(e.get('abilities', {}).items()):
            abilities_ids.append(clean_id(str(aid)))
        tier = e.get('tier') or ''
        forme = e.get('forme') or ''
        base_species = clean_id(e.get('baseSpecies') or name)
        entry = {
            'name': name,
            'num': int(num) if num.isdigit() else None,
            'types': types,
            'base_stats': e.get('baseStats', {}),
            'abilities': {'0': abilities_ids[0]} if len(abilities_ids) > 0 else {},
            'tier': tier,
            'forme': forme,
            'base_species': base_species,
            'learnset': gen9_learnsets.get(clean_id(name), []),
        }
        with open(os.path.join(out_dir, 'pokemon', f'{pid}.json'), 'w') as f:
            json.dump(entry, f)

if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])