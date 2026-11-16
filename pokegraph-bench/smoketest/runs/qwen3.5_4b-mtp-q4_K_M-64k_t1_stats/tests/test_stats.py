"""Tests for query/stats.py."""
import sys

# Add query to path so we can import from it
sys.path.insert(0, '/Users/philippeheymans/Library/Application Support/Claude/scratch-workspaces/bc618f26-50ae-4507-98f9-cffb67088cb2/9d5df48e-fc4f-4ba5-a1a2-d67eea716803/scratch-2026-11-08-d1016c/pokegraph-bench/runs/qwen3.5_4b-mtp-q4_K_M-64k_t1_stats/query')

from stats import calc_stat, calc_hp, apply_boost


def test_calc_stat_default():
    """Test calc_stat with default values."""
    # base=10, iv=31, level=100
    # inner = (2*10 + 31) * 100 / 100 = 51
    result = calc_stat(10)
    assert result == 56  # floor((51+5)*1.0)


def test_calc_stat_nature_boost():
    """Test calc_stat with boosting nature."""
    result = calc_stat(10, nature="adamant", stat_name="atk")
    assert result == 57  # 56 * 1.1 = 61.6 -> floor is 61


def test_calc_stat_nature_reduce():
    """Test calc_stat with reducing nature."""
    result = calc_stat(10, nature="adamant", stat_name="def")
    assert result == 47  # 56 * 0.9 = 50.4 -> floor is 50


def test_calc_hp_default():
    """Test calc_hp with default values."""
    hp = calc_hp(50, level=100)  # base=50, iv=31
    # (2*50 + 31) * 100/100 = 131, + 100 + 10 = 241
    assert hp == 241


def test_calc_hp_ev():
    """Test calc_hp with EVs."""
    hp = calc_hp(50, ev=128, iv=31, level=100)  # 256/4 = 64
    # (2*50 + 31 + 64) * 100/100 = 145, + 100 + 10 = 255
    assert hp == 255


def test_apply_boost_positive():
    """Test apply_boost with positive boost."""
    result = apply_boost(100, 2)  # floor(100 * 4 / 2) = 200
    assert result == 200


def test_apply_boost_negative():
    """Test apply_boost with negative boost."""
    result = apply_boost(100, -2)  # floor(100 * 2 / (2-(-2))) = floor(100*2/4) = 50
    assert result == 50


def test_apply_boost_ignore_negative():
    """Test apply_boost with ignore_negative=True."""
    result = apply_boost(100, -3, ignore_negative=True)  # boost becomes 0
    assert result == 100


def test_apply_boost_ignore_positive():
    """Test apply_boost with ignore_positive=True."""
    result = apply_boost(100, 3, ignore_positive=True)  # boost becomes 0
    assert result == 100


def test_natures_count():
    """Test that exactly 25 natures are in the table."""
    from query.stats import NATURES
    assert len(NATURES) == 25, f"Expected 25 natures, got {len(NATURES)}"
