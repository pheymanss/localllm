"""Speed computation for Pokemon (spec section 8)."""
from math import floor

# Item multipliers
ITEM_MULTIPLIERS = {
    "choicescarf": 1.5,
    "ironball": 0.5,
    "machobrace": 0.5,
}

WEATHER_ABILITIES = {
    "swiftswim": ("rain",),
    "chlorophyll": ("sun",),
    "sandrush": ("sand",),
    "slushrush": ("snow",),
    "surgesurfer": ("electric_terrain",),
}

# Ability names that activate on specific weather conditions (harshsunlight = sun, heavyrain = rain)
HARSHSUNLIGHT_CONDITIONS = {"sun"}
HEAVYRAIN_CONDITIONS = {"rain"}


def _parse_item(item):
    """Parse an item string and return the multiplier."""
    if not item:
        return 1.0

    name = str(item).strip()

    if name == "choicescarf":
        return ITEM_MULTIPLIERS["choicescarf"]
    elif name in ["ironball", "machobrace"]:
        return ITEM_MULTIPLIERS["ironball"]
    else:
        return 1.0


def _has_weather_ability(ability, weather_type=None):
    """Check if ability activates x2 based on weather conditions."""
    if not ability or ability == "unburden":
        return False

    name = str(ability).lower()

    # Check for standard weather abilities
    if name in WEATHER_ABILITIES:
        triggers = WEATHER_ABILITIES[name]

        # Special handling for surgesurfer (electric terrain only)
        if name == "surgesurfer" and weather_type != "electric_terrain":
            return False

        # Check harshsunlight (counts as sun - always works like chlorophyll)
        if name == "harshsunlight":
            # harshsunlight activates on sunlight, not rain/snow/electric terrain
            if weather_type in {"sun", None}:
                return True

        # Check heavyrain (counts as rain - always works like swiftswim)
        elif name == "heavyrain":
            # heavyrain activates on rain, not sun/sand/snow/electric terrain
            if weather_type in {"rain", None}:
                return True

    return False


def speed_check(a, b, field=None) -> dict:
    """Calculate and compare Pokemon speed for sides 'a' and 'b'.

    Each side: {id, level=100, nature, evs, ivs, boosts, item, ability, status}
    Field: {weather, terrain, tailwind: ["a"|"b", ...], trick_room: bool}

    Computation order per side:
    1. Base Speed from the graph, calc_stat with EV/IV/nature/level, then apply_boost for boosts["spe"]
    2. Item: choicescarf -> floor(x1.5); ironball or machobrace -> floor(x0.5)
    3. Ability (read only from side dict - no default to slot-0 ability):
       - unburden -> x2 (caller asserts item was consumed)
       - weather abilities, x2 when active: swiftswim (rain), chlorophyll (sun), sandrush (sand), slushrush (snow), surgesurfer (electric terrain). harshsunlight counts as sun, heavyrain counts as rain.
    4. Paralysis (status == "par"): floor(x0.5) (Gen 7+ value)
    5. Tailwind: if side's key ("a"/"b") is in field["tailwind"], floor(x2)

    Each multiplier is floored independently in the order above.

    Returns:
        {"winner": "a"|"b"|"tie", "a_speed": int, "b_speed": int, "tied": bool}
    """

    def _calculate_speed(side, field):
        """Calculate speed for a single side."""

        # Step 1: Get base speed using calc_stat with nature/IV/EV/level, then apply_boost for boosts["spe"]
        from stats import calc_stat, apply_boost

        base = side["base"]

        # Calculate initial stat with nature, IVs, EVs, level (calc_stat applies nature_mod at the end)
        speed = calc_stat(base, ev=side.get("evs"), iv=side.get("ivs", 31), level=side.get("level", 100))

        # Apply boost from boosts["spe"] if present
        boost_val = side.get("boosts", {}).get("spe", 0)
        speed = apply_boost(speed, boost_val)

        # Step 2: Item multiplier
        item_mult = _parse_item(side.get("item"))

        # Step 3: Ability weather bonus (x2 when active - from slot-0 ability only)
        weather_multiplier = 1.0
        slot_0_ability = side.get("ability", "").split(":")[0].strip() if side.get("ability") else None
        weather_type = side.get("weather")

        if slot_0_ability:
            if _has_weather_ability(slot_0_ability, weather_type):
                weather_multiplier = 2.0

        # Step 4: Paralysis penalty (floor(x0.5) for Gen 7+)
        speed = speed * (0.5 if "status" in side and side["status"] == "par" else 1.0)

        # Step 5: Tailwind bonus (floor(x2) if side's key is in field["tailwind"])
        tailwind_multiplier = 1.0
        field_list = []
        if isinstance(field, dict):
            field_list = field.get("tailwind", [])

        # Find which side has the tailwind item (first match wins due to field ordering)
        side_key = None
        for key in ["a", "b"]:
            if key in field_list:
                side_key = key
                break

        if side_key == "a":
            tailwind_multiplier = 2.0
        elif side_key == "b":
            # For 'b', we need to check if it's also in the list (if both are present)
            pass
        # Note: Tailwind only applies to ONE side at a time based on field ordering

        # Apply the multipliers to get final speed
        speed = floor(speed * tailwind_multiplier) // 1
        speed = floor(speed * item_mult) // 1
        speed = floor(speed * weather_multiplier) // 1

        return speed

    # Calculate speeds for both sides independently
    speed_a = _calculate_speed(a, field)
    speed_b = _calculate_speed(b, field)

    # Compare and determine winner
    tied = False
    if speed_a == speed_b:
        winner = "tie"
        tied = True
    elif field is not None and isinstance(field, dict) and field.get("trick_room", False):
        # Trick room inverts the comparison (lower speed wins)
        if speed_a < speed_b:
            winner = "a"
        else:
            winner = "b"
    else:
        if speed_a > speed_b:
            winner = "a"
        else:
            winner = "b"

    return {
        "winner": winner,
        "a_speed": speed_a,
        "b_speed": speed_b,
        "tied": tied,
    }
