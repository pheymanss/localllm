"""Reference loader. usage: python load.py <knowledge_dir> <db_path>"""
import csv, glob, json, os, shutil, sys, tempfile
import kuzu
DDL = ["CREATE NODE TABLE Type(name STRING, PRIMARY KEY(name))",
 "CREATE NODE TABLE Nature(name STRING, boosted_stat STRING, reduced_stat STRING, PRIMARY KEY(name))",
 "CREATE NODE TABLE Ability(id STRING, name STRING, description STRING, PRIMARY KEY(id))",
 "CREATE NODE TABLE Item(id STRING, name STRING, description STRING, PRIMARY KEY(id))",
 "CREATE NODE TABLE Move(id STRING, name STRING, type STRING, category STRING, base_power INT64, accuracy DOUBLE, priority INT64, pp INT64, target STRING, description STRING, PRIMARY KEY(id))",
 "CREATE NODE TABLE Pokemon(id STRING, name STRING, forme STRING, base_species STRING, tier STRING, hp INT64, atk INT64, def INT64, spa INT64, spd INT64, spe INT64, PRIMARY KEY(id))",
 "CREATE REL TABLE IS_TYPE(FROM Move TO Type)", "CREATE REL TABLE EFFECTIVE_VS(FROM Type TO Type, multiplier DOUBLE)",
 "CREATE REL TABLE HAS_TYPE(FROM Pokemon TO Type, slot INT64)", "CREATE REL TABLE HAS_ABILITY(FROM Pokemon TO Ability, slot STRING)",
 "CREATE REL TABLE CAN_LEARN(FROM Pokemon TO Move)"]
def main(k, db):
    if os.path.isdir(db): shutil.rmtree(db)
    elif os.path.exists(db): os.remove(db)
    J = lambda n: json.load(open(os.path.join(k, n)))
    chart, nat, ab, it, mv, ls = J("type_chart.json"), J("natures.json"), J("abilities.json"), J("items.json"), J("moves.json"), J("learnsets.json")
    mons = {os.path.basename(p)[:-5]: json.load(open(p)) for p in glob.glob(os.path.join(k, "pokemon", "*.json"))}
    conn = kuzu.Connection(kuzu.Database(db))
    for d in DDL: conn.execute(d)
    tmp = tempfile.mkdtemp()
    def copy(table, header, rows):
        p = os.path.join(tmp, table + ".csv")
        with open(p, "w", newline="") as f:
            wr = csv.writer(f); wr.writerow(header); wr.writerows(rows)
        conn.execute(f"COPY {table} FROM '{p}' (HEADER=TRUE)")
    types = sorted(chart)
    copy("Type", ["name"], [[t] for t in types])
    copy("Nature", ["name", "boosted_stat", "reduced_stat"], [[n, v["boosted"] or "", v["reduced"] or ""] for n, v in nat.items()])
    copy("Ability", ["id", "name", "description"], [[i, v["name"], v["desc"] or ""] for i, v in ab.items()])
    copy("Item", ["id", "name", "description"], [[i, v["name"], v["desc"] or ""] for i, v in it.items()])
    copy("Move", ["id","name","type","category","base_power","accuracy","priority","pp","target","description"],
         [[i, v["name"], v["type"], v["category"], v["base_power"], -1.0 if v["accuracy"] is True else float(v["accuracy"]), v["priority"], v["pp"], v["target"], v["desc"] or ""] for i, v in mv.items()])
    copy("Pokemon", ["id","name","forme","base_species","tier","hp","atk","def","spa","spd","spe"],
         [[i, v["name"], v["forme"], v["base_species"], v["tier"]] + [v["base_stats"][s] for s in ("hp","atk","def","spa","spd","spe")] for i, v in mons.items()])
    copy("IS_TYPE", ["from", "to"], [[i, v["type"]] for i, v in mv.items() if v["type"] in chart])
    copy("EFFECTIVE_VS", ["from", "to", "multiplier"], [[a, d, m] for d, row in chart.items() for a, m in row.items()])
    copy("HAS_TYPE", ["from", "to", "slot"], [[i, t, n + 1] for i, v in mons.items() for n, t in enumerate(v["types"]) if t in chart])
    copy("HAS_ABILITY", ["from", "to", "slot"], [[i, a, s] for i, v in mons.items() for s, a in v["abilities"].items() if a in ab])
    copy("CAN_LEARN", ["from", "to"], [[i, m] for i, v in mons.items() for m in ls.get(i, []) if m in mv])
    for t in ["Type","Nature","Ability","Item","Move","Pokemon"]:
        print(t, conn.execute(f"MATCH (n:{t}) RETURN count(n)").get_next()[0])
    for t in ["IS_TYPE","EFFECTIVE_VS","HAS_TYPE","HAS_ABILITY","CAN_LEARN"]:
        print(t, conn.execute(f"MATCH ()-[r:{t}]->() RETURN count(r)").get_next()[0])
if __name__ == "__main__": main(sys.argv[1], sys.argv[2])
