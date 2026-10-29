"""The python that flaps: its height, speed and tilt."""
from .motion import approach, sine
from .tuning import FLAP, GRAVITY, MAX_FALL


class Bird:
    __slots__ = ("x", "y", "home", "vy", "angle")

    def __init__(self, x, y):
        self.x, self.y, self.home = x, y, y
        self.vy = 0.0
        self.angle = 0.0

    def flap(self):
        self.vy = FLAP

    def fall(self, dt):
        self.vy = min(self.vy + GRAVITY * dt, MAX_FALL)
        self.y += self.vy * dt
        # Nose up while rising, then down as the fall gathers speed.
        self.angle = approach(self.angle, max(-25.0, min(90.0, self.vy * 0.12)), 8, dt)
        assert -25.0 <= self.angle <= 90.0

    def hover(self, clock):
        """Bob gently while the game waits for the first flap."""
        self.y = self.home + 9 * sine(clock * 5)
        self.angle = 0.0
