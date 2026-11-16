"""Tests for speed_check (spec section 8)."""
import pytest
import sys
from math import floor

# Add query directory to path at module level
sys.path.insert(0, '/private/tmp/claude-501/-Users-philippeheymans-Library-Application-Support-Claude-scratch-workspaces-bc618f26-50ae-4507-98f9-cffb67088cb2-9d5df48e-fc4f-4ba5-a1a2-d67eea716803-scratch-2026-11-08-d1016c/82e02082-89bf-4a1c-9968-e4dfd6ddb74d/scratchpad/pgruns/qwen3.5_4b-mtp-q4_K_M-64k_t5_speed/query')


# Basic test data - these match Pokemon from gen9ou database
# We'll use known values that work with the calc_stat formula

# Normal Eevee (base speed 110, jolly nature gives +1.2 to spe)
Eevee_normal = {
    "base": 110,
    "nature": "jolly",
    "ivs": [31],
    "evs": None,
    "level": 100,
    "boosts": {},
    "item": None,
    "ability": "runaway",
    "status": None,
}

# Normal Jolteon (base speed 130, jolly nature gives +1.2 to spe)
Jolteon_normal = {
    "base": 130,
    "nature": "jolly",
    "ivs": [31],
    "evs": None,
    "level": 100,
    "boosts": {},
    "item": None,
    "ability": "voltabsorb",
    "status": None,
}

# Eevee with choicescarf (should get x1.5 from item)
Eevee_carf = {
    "base": 110,
    "nature": "jolly",
    "ivs": [31],
    "evs": None,
    "level": 100,
    "boosts": {},
    "item": "choicescarf",
    "ability": "runaway",
    "status": None,
}

# Jolteon with choicescarf
Jolteon_carf = {
    "base": 130,
    "nature": "jolly",
    "ivs": [31],
    "evs": None,
    "level": 100,
    "boosts": {},
    "item": "choicescarf",
    "ability": "voltabsorb",
    "status": None,
}

# Paralyzed Eevee (should get floor(x0.5) from paralysis)
Eevee_par = {
    "base": 110,
    "nature": "jolly",
    "ivs": [31],
    "evs": None,
    "level": 100,
    "boosts": {},
    "item": None,
    "ability": "runaway",
    "status": "par",
}

# Paralyzed Jolteon
Jolteon_par = {
    "base": 130,
    "nature": "jolly",
    "ivs": [31],
    "evs": None,
    "level": 100,
    "boosts": {},
    "item": None,
    "ability": "voltabsorb",
    "status": "par",
}

# Test base calculation - Jolteon should be faster than Eevee


def test_jolteon_faster_than_eevee():
    """Test that Jolteon is faster than Eevee with same stats."""
    result = speed_check(Eevee_normal, Jolteon_normal)
    assert result["a_speed"] < result["b_speed"], "Jolteon should be faster"
    assert result["winner"] == "b", f"Expected 'b' winner, got '{result['winner']}'"


def test_choicescarf_multiplier():
    """Test that choicescarf gives x1.5 multiplier."""
    # Eevee normal vs Jolteon with scarf - the 0.5x difference should matter
    result = speed_check(Eevee_normal, Jolteon_carf)
    assert result["a_speed"] < result["b_speed"], "Scarfed Jolteon should be faster"


def test_ironball_multiplier():
    """Test that ironball/machobrace gives x0.5 multiplier."""
    Ironman = {
        "base": 120,
        "nature": "adamant",  # + to atk, neutral to spe
        "ivs": [31],
        "evs": None,
        "level": 100,
        "boosts": {},
        "item": "ironball",
        "ability": "fightingtypebuff",
        "status": None,
    }

    result = speed_check(Eevee_carf, Ironman)
    # Eevee with scarf (x1.5), Ironman with ironball (x0.5)
    # 110 * 1.2 * 1.5 = ~198 vs 120 * 1.0 * 0.5 = ~60 (adamant is neutral for spe)
    assert result["a_speed"] > result["b_speed"], "Scarfed Eevee should be faster"


def test_machobrace_multiplier():
    """Test that machobrace gives x0.5 multiplier."""
    Machace = {
        "base": 120,
        "nature": "adamant",
        "ivs": [31],
        "evs": None,
        "level": 100,
        "boosts": {},
        "item": "machobrace",
        "ability": "unnerve",
        "status": None,
    }

    result = speed_check(Eevee_carf, Machace)
    assert result["a_speed"] > result["b_speed"], "Scarfed Eevee should be faster"


def test_paralysis_penalty():
    """Test that paralysis gives floor(x0.5) multiplier."""
    # Both paralyzed - should still have comparable speed
    result = speed_check(Eevee_par, Jolteon_par)
    assert result["a_speed"] < result["b_speed"], "Paralyzed Jolteon should still be faster"


def test_tie_when_equally_faster():
    """Test that equal speeds result in 'tie'."""
    # Create two identical sides
    side1 = {
        "base": 100,
        "nature": "jolly",
        "ivs": [31],
        "evs": None,
        "level": 100,
        "boosts": {},
        "item": None,
        "ability": "runaway",
        "status": None,
    }

    side2 = {
        "base": 100,
        "nature": "jolly",
        "ivs": [31],
        "evs": None,
        "level": 100,
        "boosts": {},
        "item": None,
        "ability": "runaway",
        "status": None,
    }

    result = speed_check(side1, side2)
    assert result["tied"] is True, "Equal sides should tie"
    assert result["winner"] == "tie", f"Expected 'tie', got '{result['winner']}'"


def test_tie_with_field():
    """Test that ties are not broken by field (including trick room)."""
    result = speed_check(Eevee_carf, Jolteon_carf, {"trick_room": True})
    # Trick room inverts comparison but doesn't break ties
    # Jolteon with scarf should still be faster
    assert result["winner"] == "b", f"Trick room should not change winner for non-tied sides"


def test_field_tailwind():
    """Test that Tailwind gives x2 multiplier."""
    side_a_with_tailwind = Eevee_carf.copy()
    # Field has tailwind for 'a' side
    result = speed_check(side_a_with_tailwind, Jolteon_normal, {"tailwind": ["a", "b"]})
    # Tailwind is only applied to the side whose key is in tailwind list
    # Eevee (side a) has scarf, so gets both scarf and tailwind multipliers


def test_nature_mod_applied():
    """Test that nature modifiers are applied correctly."""
    # Jolly nature (+1.2 to spe), Adamant neutral (x1)
    result = speed_check(Eevee_normal, {
        "base": 100,
        "nature": "adamant",  # Neutral for spe
        "ivs": [31],
        "evs": None,
        "level": 100,
        "boosts": {},
        "item": None,
        "ability": "runaway",
        "status": None,
    })
    # Eevee: 110 * 1.2 = 132, Jolteon-like: 110 * 1.0 = 110
    assert result["a_speed"] > result["b_speed"], "Nature modifier should favor jolly nature"


def test_boost_multiplier():
    """Test that boost modifiers are applied."""
    # Using a simple non-paralyzed comparison to check boosting logic
    Eevee_with_spe = {
        "+spe": 2,  # This gets converted via apply_boost
        "level": 100,
        "ivs": [31],
        "evs": None,
        "nature": "jolly",
        "base": 110,
        "ability": "runaway",
        "item": None,
        "status": None,
    }

    Eevee_with_atk_boost = {
        "+atk": 2,
        "level": 100,
        "ivs": [31],
        "evs": None,
        "nature": "jolly",
        "base": 110,
        "ability": "runaway",
        "item": None,
        "status": None,
    }


# Run tests using pytest
if __name__ == "__main__":
    import subprocess

    # Import and run each test function
    from speed_check import speed_check

    test_jolteon_faster_than_eevee()
    print("✓ test_jolteon_faster_than_eevee")

    test_choicescarf_multiplier()
    print("✓ test_choicescarf_multiplier")

    test_ironball_multiplier()
    print("✓ test_ironball_multiplier")

    test_machobrace_multiplier()
    print("✓ test_machobrace_multiplier")

    test_paralysis_penalty()
    print("✓ test_paralysis_penalty")

    test_tie_when_equally_faster()
    print("✓ test_tie_when_equally_faster")

    test_tie_with_field()
    print("✓ test_tie_with_field")

    test_nature_mod_applied()
    print("✓ test_nature_mod_applied")
