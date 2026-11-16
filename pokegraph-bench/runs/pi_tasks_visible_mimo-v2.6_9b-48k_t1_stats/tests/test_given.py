import pytest
from stats import calc_stat, calc_hp, apply_boost
@pytest.mark.parametrize("args,exp", [
 ((102,252,31,100,"jolly","spe"),333), ((106,0,31,100,"hardy","def"),248), ((130,252,31,100,"jolly","atk"),359),
 ((130,252,31,100,"adamant","atk"),394), ((130,252,31,100,"modest","atk"),323), ((100,0,0,100,"hardy","atk"),205),
 ((100,0,None,100,None,"atk"),236), ((130,252,31,50,"adamant","atk"),200), ((80,4,31,100,"modest","spa"),216),((80,4,31,100,"timid","spa"),197)])
def test_calc_stat(args, exp): assert calc_stat(*args) == exp
@pytest.mark.parametrize("args,exp", [((91,252,31,100),386), ((91,252,31,50),198), ((108,0,0,100),326), ((108,0,None,100),357)])
def test_calc_hp(args, exp): assert calc_hp(*args) == exp
def test_defaults(): assert calc_stat(100, stat_name="atk") == 236 and calc_hp(100) == 341
@pytest.mark.parametrize("args,exp", [((100,1),150),((100,6),400),((100,8),400),((100,-1),66),((100,-6),25),((100,-9),25),((333,2),666),((100,0),100),
 ((100,-2,True,False),100),((100,2,False,True),100),((100,2,True,False),200),((100,-2,False,True),50)])
def test_apply_boost(args, exp): assert apply_boost(*args) == exp
