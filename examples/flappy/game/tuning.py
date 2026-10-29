"""The numbers that shape the game: the window, the physics, the pipes."""
WIDTH, HEIGHT = 480, 720
GROUND = 640            # top of the ground strip
GRAVITY = 1900.0        # pixels per second squared
FLAP = -560.0           # vertical speed right after a flap
MAX_FALL = 900.0
SPEED = 170.0           # how fast the world scrolls
GAP = 190               # opening between the two pipes of a pair
PIPE_WIDTH = 78
SPACING = 250           # distance between pairs
BIRD_X = 140
BIRD_SIZE = 56          # the sprite's drawn height
HIT_RADIUS = 21         # the bird's hitbox, a little inside the sprite

# A player's own numbers, from a custom.py beside this file, which the game
# does not ship. The import is guarded, so spyc leaves it out when the file
# is missing, and at run time it fails here just as it would unbundled.
try:
    from .custom import *
except ImportError:
    pass
