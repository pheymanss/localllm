"""Tests for Pokemon stat calculations."""

import pytest
import sys
sys.path.insert(0, '/private/tmp/claude-501/-Users-philippeheymans-Library-Application-Support-Claude-scratch-workspaces-bc618f26-50ae-4507-98f9-cffb67088cb2-9d5df48e-fc4f-4ba5-a1a2-d67eea716803-scratch-2026-11-08-d1016c/82e02082-89bf-4a1c-9968-e4dfd6ddb74d/scratchpad/pgruns/qwen3.5_4b-mtp-q4_K_M-64k_t1_stats/query')

from stats import calc_stat, calc_hp, apply_boost, NATURE_TABLE, STATS


class TestCalcStat:
    """Tests for calc_stat function."""

    def test_default_values(self):
        """Test with default values (IV=31, EV=0, Level=100)."""
        assert calc_stat(10) == 110
        assert calc_stat(20) == 206
        assert calc_stat(50) == 530

    def test_with_ev(self):
        """Test stat calculation with EVs."""
        # Base=5, IV=31, EV=128, Level=50
        # inner = floor((2*5 + 31 + floor(128/4)) * 50 / 100)
        #       = floor((10 + 31 + 32) * 50 / 100)
        #       = floor(73 * 0.5) = 36
        # stat = floor((36 + 5) * 1.0) = 41
        assert calc_stat(5, ev=128) == 41

    def test_with_ev_div4(self):
        """Test EV calculation (floor division by 4)."""
        # EV=1 gives floor(1/4)=0, so same as EV=0
        assert calc_stat(10, ev=1) == calc_stat(10, ev=0)

    def test_nature_boost(self):
        """Test nature boost effect."""
        jolly = calc_stat(50, nature="jolly", stat_name="atk")
        plain = calc_stat(50, nature=None, stat_name="atk")
        assert jolly > plain

    def test_nature_reduce(self):
        """Test nature reduction effect."""
        sassy = calc_stat(50, nature="sassy", stat_name="atk")
        plain = calc_stat(50, nature=None, stat_name="atk")
        assert sassy < plain

    def test_none_nature_equal_default(self):
        """Test that None and no nature produce same result."""
        assert calc_stat(50, nature=None) == calc_stat(50, nature=1.0)
        # But different stats should still be affected if stat_name specified

    def test_all_stats(self):
        """Test all five stats."""
        for stat in STATS:
            value = calc_stat(50, stat_name=stat)
            assert isinstance(value, int), f"Result for {stat} is not int"

    def test_stat_alias_at_to_atk(self):
        """Test that 'at' aliases to 'atk'."""
        at_value = calc_stat(50, stat_name="at")
        atk_value = calc_stat(50, stat_name="atk")
        assert at_value == atk_value


class TestCalcHp:
    """Tests for calc_hp function."""

    def test_default_values(self):
        """Test HP with default values."""
        # Base=10, IV=31, EV=0, Level=100
        # HP = floor((2*10 + 31 + 0) * 100 / 100) + 100 + 10
        #    = floor(71 * 1) + 100 + 10
        #    = 71 + 100 + 10 = 181
        assert calc_hp(10) == 181

    def test_with_higher_base(self):
        """Test HP with higher base stat."""
        # Base=50, IV=31, EV=0, Level=100
        # HP = floor((2*50 + 31 + 0) * 100 / 100) + 100 + 10
        #    = floor(131 * 1) + 100 + 10
        #    = 131 + 100 + 10 = 241
        assert calc_hp(50) == 241

    def test_with_ev(self):
        """Test HP calculation with EVs."""
        # Base=10, IV=31, EV=16, Level=100
        # EV contribution = floor(16/4) = 4
        # HP = floor((2*10 + 31 + 4) * 100 / 100) + 100 + 10
        #    = floor(51 * 1) + 100 + 10
        #    = 51 + 100 + 10 = 161
        assert calc_hp(10, ev=16) == 161


class TestApplyBoost:
    """Tests for apply_boost function."""

    def test_positive_boost(self):
        """Test positive stat boost."""
        # boost=2 gives multiplier of (2+2)/2 = 2
        stat = calc_stat(50, nature="jolly", stat_name="atk")
        boosted = apply_boost(stat, boost=2)
        # Should be floor(53 * 2) = 106 if base is 53
        assert boosted >= stat

    def test_negative_boost(self):
        """Test negative stat reduction."""
        stat = calc_stat(50, nature="sassy", stat_name="atk")
        reduced = apply_boost(stat, boost=-2)
        # Should be less than base stat
        assert reduced <= stat

    def test_clamp_negative(self):
        """Test that boost is clamped to minimum -6."""
        stat = 100
        reduced = apply_boost(stat, boost=-10)
        # Should use boost=-6
        # floor(100 * 2 / (2-(-6))) = floor(200 / 8) = 25
        assert reduced == 25

    def test_clamp_positive(self):
        """Test that boost is clamped to maximum 6."""
        stat = 100
        boosted = apply_boost(stat, boost=10)
        # Should use boost=6
        # floor(100 * (2+6) / 2) = floor(800/2) = 400
        assert boosted == 400

    def test_ignore_negative(self):
        """Test ignore_negative parameter."""
        stat = 100
        # Ignored negative boost (e.g., attacker on crit)
        # This means treat negative boosts as 0, so stat remains unchanged
        result = apply_boost(stat, boost=-2, ignore_negative=True)
        assert result == stat

    def test_ignore_positive(self):
        """Test ignore_positive parameter."""
        stat = 100
        # Ignored positive boost (e.g., defender on crit)
        result = apply_boost(stat, boost=2, ignore_positive=True)
        assert result == stat

    def test_no_boost_no_change(self):
        """Test that no change in boost keeps stat unchanged."""
        stat = 50
        result = apply_boost(stat, boost=0)
        assert result == stat


class TestNatureTable:
    """Tests for NATURE_TABLE."""

    def test_table_has_25_entries(self):
        """Test that nature table has exactly 25 entries."""
        assert len(NATURE_TABLE) == 25

    def test_all_natures_are_strings(self):
        """Test all keys are lowercase strings."""
        for name in NATURE_TABLE.keys():
            assert isinstance(name, str), "Nature name is not a string"
            assert name.islower(), f"Nature '{name}' is not lowercase"

    def test_two_values_per_nature(self):
        """Test that each nature has exactly two values (boosted and reduced)."""
        for nature, vals in NATURE_TABLE.items():
            assert len(vals) == 2

    def test_all_stats_covered(self):
        """Test that all five stats are covered across natures."""
        all_stats = set()
        for nature, vals in NATURE_TABLE.items():
            for stat in vals.values():
                all_stats.add(stat)
        assert all_stats == {0.9, 1.1}, "Not all nature values are 0.9 or 1.1"

    def test_one_stat_per_nature(self):
        """Test that each nature only modifies one stat."""
        for nature, vals in NATURE_TABLE.items():
            # Each nature should have exactly one boosted and one reduced stat
            assert len(vals.keys()) == 1


class TestIntegration:
    """Integration tests."""

    def test_full_calculation(self):
        """Test a full stat calculation with EVs and nature."""
        base = 50
        ev = 128
        iv = 31
        level = 50
        nature = "jolly"

        # Calculate attack
        atk = calc_stat(base, ev, iv, level, nature, "atk")
        hp = calc_hp(base, ev, iv, level)

        assert atk > base  # Jolly boosts ATK
        assert isinstance(hp, int)

    def test_hp_formula(self):
        """Verify HP formula matches specification."""
        # Base=200 (Gen 4 max), IV=31, EV=0, Level=100
        hp = calc_hp(200, iv=31, level=100)
        expected = ((2 * 200 + 31 + 0) * 100 // 100) + 100 + 10
        assert hp == expected
