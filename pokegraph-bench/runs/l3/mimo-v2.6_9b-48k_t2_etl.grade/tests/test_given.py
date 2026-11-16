import json, os, subprocess, sys, glob, pytest
OUT = "knowledge_hidden"
@pytest.fixture(scope="module", autouse=True)
def built():
    import shutil; shutil.rmtree(OUT, ignore_errors=True)
    r = subprocess.run([sys.executable, "query/etl.py", "raw", OUT], capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
def J(n): return json.load(open(os.path.join(OUT, n)))
def test_files():
    for n in ["type_chart.json","natures.json","items.json","abilities.json","moves.json","learnsets.json"]: assert os.path.exists(os.path.join(OUT, n)), n
def test_type_chart():
    tc = J("type_chart.json"); assert len(tc) == 18 and "stellar" not in tc
    assert tc["fire"]["ground"] == 2.0 and tc["flying"]["ground"] == 0.0 and tc["steel"]["poison"] == 0.0 and tc["water"]["fire"] == 0.5 and tc["ghost"]["normal"] == 0.0
    assert all(k in tc for row in tc.values() for k in row), "non-type keys present"
    assert all(v != 1.0 for row in tc.values() for v in row.values()) and "normal" not in tc["fire"]
    assert sum(len(r) for r in tc.values()) == 120
def test_natures():
    n = J("natures.json"); assert len(n) == 25
    assert n["jolly"] == {"boosted":"spe","reduced":"spa"} and n["hardy"] == {"boosted":None,"reduced":None}
    assert sum(1 for v in n.values() if v["boosted"] is None) == 5
def test_items_abilities():
    it, ab = J("items.json"), J("abilities.json")
    assert "choicescarf" in it and "charizarditex" not in it and it["leftovers"]["name"] == "Leftovers"
    assert "levitate" in ab and ab["levitate"]["name"] == "Levitate" and 280 <= len(ab) <= 330 and 250 <= len(it) <= 330
def test_moves():
    m = J("moves.json"); e = m["earthquake"]
    assert e["type"] == "ground" and e["category"] == "physical" and e["base_power"] == 100 and e["accuracy"] == 100 and e["priority"] == 0 and e["pp"] == 10 and e["target"] == "allAdjacent"
    assert m["makeitrain"]["category"] == "special" and m["swordsdance"]["category"] == "status" and m["aerialace"]["accuracy"] is True
    assert m["extremespeed"]["priority"] == 2 and m["closecombat"]["flags"].get("contact") == 1
    assert "maliciousmoonsault" not in m and 680 <= len(m) <= 760
def test_learnsets():
    l = J("learnsets.json")
    assert {"nastyplot","recover","makeitrain"} <= set(l["gholdengo"]) and "earthquake" not in l["gholdengo"]
    assert l["gholdengo"] == sorted(l["gholdengo"]) and "missingno" not in l and "bulbasaur" in l and 850 <= len(l) <= 960
def test_pokemon():
    files = glob.glob(os.path.join(OUT, "pokemon", "*.json")); assert 1300 <= len(files) <= 1500
    g = json.load(open(os.path.join(OUT, "pokemon", "garchomp.json")))
    assert g["types"] == ["dragon","ground"] and g["base_stats"]["spe"] == 102 and g["abilities"] == {"0":"sandveil","H":"roughskin"}
    assert g["name"] == "Garchomp" and g["num"] == 445 and "earthquake" in g["learnset"] and g["tier"]
    lt = json.load(open(os.path.join(OUT, "pokemon", "landorustherian.json"))); assert lt["base_species"] == "Landorus" and lt["forme"] == "Therian"
    assert not os.path.exists(os.path.join(OUT, "pokemon", "syclant.json")), "CAP species not filtered"
    rw = json.load(open(os.path.join(OUT, "pokemon", "rotomwash.json"))); assert rw["types"] == ["electric","water"]
