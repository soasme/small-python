"""Pairs of pipes scrolling past, each with a gap at a random height."""
from .collide import circle_hits_rect
from .tuning import GAP, GROUND, HIT_RADIUS, PIPE_WIDTH, SPACING, SPEED, WIDTH

MARGIN = 70             # the least pipe above and below a gap


class Random:
    """xorshift32: the core has no random module, and a seed replays a run."""

    def __init__(self, seed):
        self.state = seed & 0xFFFFFFFF or 1

    def between(self, low, high):
        s = self.state
        s ^= (s << 13) & 0xFFFFFFFF
        s ^= s >> 17
        s ^= (s << 5) & 0xFFFFFFFF
        self.state = s
        return low + s % (high - low + 1)


class Pipe:
    __slots__ = ("x", "gap_y", "passed")

    def __init__(self, x, gap_y):
        self.x, self.gap_y, self.passed = x, gap_y, False

    def rects(self):
        """The upper and lower pipe as (x, y, w, h)."""
        top = self.gap_y - GAP / 2
        bottom = self.gap_y + GAP / 2
        return (self.x, 0, PIPE_WIDTH, top), (self.x, bottom, PIPE_WIDTH, GROUND - bottom)


class Pipes:
    def __init__(self, seed):
        self.random = Random(seed)
        self.reset()

    def reset(self):
        self.pairs = []
        self.next_x = WIDTH + 160

    def update(self, dt, bird_x):
        """Scroll, spawn and drop pairs; return the points scored."""
        points = 0
        for pipe in self.pairs:
            pipe.x -= SPEED * dt
            if not pipe.passed and pipe.x + PIPE_WIDTH < bird_x:
                pipe.passed = True
                points += 1
        self.next_x -= SPEED * dt
        while self.next_x < WIDTH + PIPE_WIDTH:
            low, high = MARGIN + GAP // 2, GROUND - MARGIN - GAP // 2
            self.pairs.append(Pipe(self.next_x, self.random.between(low, high)))
            self.next_x += SPACING
        self.pairs = [pipe for pipe in self.pairs if pipe.x + PIPE_WIDTH > 0]
        return points

    def hits(self, bird):
        return any(circle_hits_rect(bird.x, bird.y, HIT_RADIUS, *rect)
                   for pipe in self.pairs for rect in pipe.rects())
