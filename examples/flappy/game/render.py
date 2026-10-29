"""Drawing a world with raylib. The sprite comes from assets.sprite, a module
pack.py generates from python.png, so the image is bundled like code."""
import raylib as rl
from assets.sprite import PYTHON_PNG

from . import themes
lazy from . import medals       # PEP 810: loads at the first game over
from .pipes import Random
from .tuning import BIRD_SIZE, GROUND, HEIGHT, PIPE_WIDTH, WIDTH

WHITE, INK = (255, 255, 255), (40, 44, 52)
LIP = 26                # height of a pipe's rim


class Renderer:
    def __init__(self):
        self.sprite = rl.load_texture(PYTHON_PNG)
        sky = Random(7)
        self.clouds = [(sky.between(0, WIDTH), sky.between(40, 300), sky.between(18, 34)) for _ in range(6)]
        self.stars = [(sky.between(0, WIDTH), sky.between(0, GROUND - 120), sky.between(1, 2)) for _ in range(60)]

    def draw(self, world):
        theme = themes.for_score(world.score)
        rl.begin_drawing()
        rl.clear_background(theme.SKY)
        self.backdrop(theme, world.scroll)
        for pipe in world.pipes.pairs:
            self.pipe(theme, *pipe.rects())
        self.ground(theme, world.scroll)
        bird = world.bird
        rl.draw_texture(self.sprite, bird.x, bird.y, BIRD_SIZE, bird.angle)
        self.overlay(world)
        if world.flash:
            rl.draw_rectangle(0, 0, WIDTH, HEIGHT, (255, 255, 255, int(200 * world.flash)))
        rl.end_drawing()

    def backdrop(self, theme, scroll):
        for x, y, size in self.stars[:theme.STARS]:
            rl.draw_circle(x, y, size, (255, 255, 230))
        # Far things move slower: clouds at a fifth of the speed, hills at a third.
        # A cloud reaches 1.8 radii (at most 62 pixels) from its center, so it
        # wraps around 70 pixels off screen, where the jump cannot be seen.
        for x, y, r in self.clouds:
            x = (x - scroll * 0.2) % (WIDTH + 140) - 70
            for dx, dy, k in ((0, 0, 1.0), (r, 6, 0.8), (-r, 8, 0.7)):
                rl.draw_circle(x + dx, y + dy, r * k, theme.CLOUD)
        # Hills alternate small and large, so the row repeats every two hills.
        offset = scroll / 3 % 320
        for i in range(-1, WIDTH // 160 + 3):
            rl.draw_circle(i * 160 - offset + 80, GROUND + 10, 90 + 20 * (i % 2), theme.HILLS)

    def pipe(self, theme, *rects):
        for x, y, w, h in rects:
            rl.draw_rectangle(x, y, w, h, theme.PIPE)
            rl.draw_rectangle(x + w - 14, y, 14, h, theme.PIPE_SHADE)
            rl.draw_rectangle(x + 8, y, 6, h, (255, 255, 255, 70))
        (x, _, _, top), (_, bottom, _, _) = rects
        for rim_y in (top - LIP, bottom):
            rl.draw_rectangle(x - 6, rim_y, PIPE_WIDTH + 12, LIP, theme.PIPE_SHADE)
            rl.draw_rectangle(x - 3, rim_y + 3, PIPE_WIDTH + 6, LIP - 6, theme.PIPE)

    def ground(self, theme, scroll):
        rl.draw_rectangle(0, GROUND, WIDTH, HEIGHT - GROUND, theme.GROUND)
        rl.draw_rectangle(0, GROUND, WIDTH, 14, theme.GRASS)
        offset = scroll % 32
        for x in range(-1, WIDTH // 32 + 2):
            rl.draw_rectangle(x * 32 - offset, GROUND + 14, 16, 6, theme.PIPE_SHADE)

    def overlay(self, world):
        match world.state:
            case "ready":
                centered("Flappy Python", 150, 48, WHITE)
                centered("Space, Up or click to flap", 420, 22, WHITE)
            case "playing" | "falling":
                centered(str(world.score), 60, 64, WHITE)
            case "over":
                self.scoreboard(world)

    def scoreboard(self, world):
        centered("Game Over", 140, 52, WHITE)
        rl.draw_rectangle(WIDTH / 2 - 150, 230, 300, 190, (250, 240, 210, 235))
        centered(f"Score  {world.score}", 260, 32, INK)
        centered(f"Best  {world.best}", 305, 32, INK)
        if earned := medals.medal(world.score):
            name, color = earned
            rl.draw_circle(WIDTH / 2, 375, 22, color)
            centered(name, 400, 18, INK)
        if world.clock > 0.6:
            centered("Space to fly again", 470, 22, WHITE)


def centered(text, y, size, color):
    """Text centered across the window, over a soft shadow."""
    x = (WIDTH - rl.measure_text(text, size)) / 2
    if color == WHITE:
        rl.draw_text(text, x + 2, y + 3, size, (0, 0, 0, 90))
    rl.draw_text(text, x, y, size, color)
