"""Medals for a finished run. The game imports this module lazily (PEP 810),
so it first runs at the first game over."""
MEDALS = (
    (40, "PLATINUM", (229, 228, 226)),
    (30, "GOLD", (255, 200, 40)),
    (20, "SILVER", (200, 205, 215)),
    (10, "BRONZE", (205, 127, 50)),
)


def medal(score):
    """The (name, color) a score earns, or None."""
    for least, name, color in MEDALS:
        if score >= least:
            return name, color
    return None
