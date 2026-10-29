"""Palettes, one module each. No import statement names them: for_score
computes the module's name, so the build includes them with -D 'game.themes.*'
and the game can gain a theme by gaining a file."""
NAMES = ("day", "dusk", "night")


def for_score(score):
    """The sky changes every ten points."""
    name = NAMES[score // 10 % len(NAMES)]
    return __import__(f"game.themes.{name}", fromlist=("SKY",))
