import pytest
from type_matchup import type_matchup
from coverage import coverage
@pytest.mark.parametrize("a,d,exp", [("ground","heatran",4.0),("ground","skarmory",0.0),("fire","corviknight",2.0),("dragon","garchomp",2.0),
 ("electric","rotomwash",1.0),("normal","gengar",0.0),("water","gastrodon",1.0),("ice","garchomp",4.0),("fighting","kingambit",4.0),("grass","toxapex",1.0),("fire","scizor",4.0)])
def test_type_matchup(a, d, exp): assert type_matchup(a, d) == exp
def test_unknown_defender():
    with pytest.raises(ValueError): type_matchup("fire", "notamon")
MV = ["earthquake","stoneedge","firepunch","swordsdance"]
@pytest.mark.parametrize("t,best,moves", [("skarmory",2.0,["firepunch"]),("heatran",4.0,["earthquake"]),("corviknight",2.0,["firepunch"]),("toxapex",2.0,["earthquake"])])
def test_coverage(t, best, moves):
    c = coverage(MV, t); assert c["best_mult"] == best and sorted(c["best_moves"]) == moves
def test_coverage_details():
    c = coverage(MV, "skarmory"); bm = c["by_move"]
    assert bm["stoneedge"]["mult"] == 1.0 and bm["earthquake"]["mult"] == 0.0
    assert bm["swordsdance"]["status_move"] is True and bm["swordsdance"]["mult"] is None
def test_coverage_edge():
    assert coverage(["earthquake"], "skarmory")["best_mult"] == 0.0
    c = coverage(["swordsdance"], "heatran"); assert c["best_mult"] is None and c["best_moves"] == []
    c = coverage(["notamove","earthquake"], "heatran"); assert c["by_move"]["notamove"]["mult"] is None and "error" in c["by_move"]["notamove"] and c["best_mult"] == 4.0
