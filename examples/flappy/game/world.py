"""One run of the game, as a small state machine:

ready -> playing -> falling -> over -> ready
"""
from .bird import Bird
from .pipes import Pipes
from .tuning import BIRD_X, GROUND, HEIGHT, HIT_RADIUS, SPEED


class World:
    def __init__(self, seed):
        self.pipes = Pipes(seed)
        self.best = 0
        self.reset()

    def reset(self):
        self.bird = Bird(BIRD_X, HEIGHT * 0.42)
        self.pipes.reset()
        self.state = "ready"
        self.score = 0
        self.clock = 0.0        # seconds in this state
        self.scroll = 0.0       # how far the ground has moved
        self.flash = 0.0        # the white flash of a crash, fading

    def enter(self, state):
        self.state, self.clock = state, 0.0

    def update(self, dt, flapped):
        self.clock += dt
        self.flash = max(0.0, self.flash - dt * 3)
        bird = self.bird
        match self.state:
            case "ready":
                self.scroll += SPEED * dt
                bird.hover(self.clock)
                if flapped:
                    self.enter("playing")
                    bird.flap()
            case "playing":
                self.scroll += SPEED * dt
                if flapped:
                    bird.flap()
                bird.fall(dt)
                if bird.y < HIT_RADIUS:
                    bird.y, bird.vy = HIT_RADIUS, 0.0
                self.score += self.pipes.update(dt, bird.x)
                if self.pipes.hits(bird) or bird.y + HIT_RADIUS >= GROUND:
                    self.crash()
            case "falling":
                bird.fall(dt)
                if bird.y + HIT_RADIUS >= GROUND:
                    bird.y = GROUND - HIT_RADIUS
                    self.enter("over")
            case "over":
                if flapped and self.clock > 0.6:
                    self.reset()

    def crash(self):
        self.flash = 1.0
        self.best = max(self.best, self.score)
        self.bird.vy = max(self.bird.vy, 0.0)
        self.enter("falling")
