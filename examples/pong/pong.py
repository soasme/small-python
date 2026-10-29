# Pong: the game logic runs on Small Python; drawing and input go through
# the host's raylib C module. W/S or Up/Down move your paddle, Space serves.
import raylib as rl

WIDTH, HEIGHT = 800, 450
PADDLE_W, PADDLE_H, PADDLE_SPEED = 12, 80, 360
BALL_R, BALL_SPEED, SPEEDUP = 8, 300, 1.06
WIN_SCORE = 7
BACKGROUND, FOREGROUND, DIM = (20, 20, 28), (235, 235, 235), (90, 90, 110)


class Paddle:
    def __init__(self, x):
        self.x, self.y, self.score = x, (HEIGHT - PADDLE_H) / 2, 0

    def move(self, dy):
        self.y = min(max(self.y + dy, 0), HEIGHT - PADDLE_H)

    def hits(self, ball):
        return (self.x - BALL_R <= ball.x <= self.x + PADDLE_W + BALL_R
                and self.y - BALL_R <= ball.y <= self.y + PADDLE_H + BALL_R)

    def draw(self):
        rl.draw_rectangle(self.x, self.y, PADDLE_W, PADDLE_H, FOREGROUND)


class Ball:
    def __init__(self):
        self.reset(1)

    def reset(self, direction):
        self.x, self.y = WIDTH / 2, HEIGHT / 2
        self.dx, self.dy = 0, 0
        self.direction = direction

    def serve(self):
        self.dx = self.direction * BALL_SPEED
        self.dy = rl.get_random_value(-BALL_SPEED, BALL_SPEED) * 0.6

    @property
    def moving(self):
        return self.dx != 0

    def bounce_off(self, paddle):
        # The farther from the paddle's centre, the steeper the return.
        offset = (self.y - (paddle.y + PADDLE_H / 2)) / (PADDLE_H / 2)
        self.dx = -self.dx * SPEEDUP
        self.dy = offset * abs(self.dx)
        self.x = paddle.x + PADDLE_W + BALL_R if self.dx > 0 else paddle.x - BALL_R

    def draw(self):
        rl.draw_circle(self.x, self.y, BALL_R, FOREGROUND)


class Game:
    def __init__(self):
        self.player = Paddle(24)
        self.computer = Paddle(WIDTH - 24 - PADDLE_W)
        self.ball = Ball()
        self.winner = None

    def update(self, dt):
        if self.winner:
            if rl.is_key_pressed(rl.KEY_SPACE):
                self.__init__()
            return
        if not self.ball.moving:
            if rl.is_key_pressed(rl.KEY_SPACE):
                self.ball.serve()
            return
        self.steer_player(dt)
        self.steer_computer(dt)
        self.move_ball(dt)

    def steer_player(self, dt):
        up = rl.is_key_down(rl.KEY_W) or rl.is_key_down(rl.KEY_UP)
        down = rl.is_key_down(rl.KEY_S) or rl.is_key_down(rl.KEY_DOWN)
        self.player.move((down - up) * PADDLE_SPEED * dt)

    def steer_computer(self, dt):
        # Follow the ball a little slower than the player can move.
        target = self.ball.y - PADDLE_H / 2
        step = PADDLE_SPEED * 0.8 * dt
        self.computer.move(max(-step, min(step, target - self.computer.y)))

    def move_ball(self, dt):
        ball = self.ball
        ball.x += ball.dx * dt
        ball.y += ball.dy * dt
        if ball.y < BALL_R or ball.y > HEIGHT - BALL_R:
            ball.y = min(max(ball.y, BALL_R), HEIGHT - BALL_R)
            ball.dy = -ball.dy
        for paddle in self.player, self.computer:
            if paddle.hits(ball) and (ball.dx < 0) == (paddle is self.player):
                ball.bounce_off(paddle)
        if ball.x < 0:
            self.point(self.computer, -1)
        elif ball.x > WIDTH:
            self.point(self.player, 1)

    def point(self, scorer, direction):
        scorer.score += 1
        self.ball.reset(direction)
        if scorer.score == WIN_SCORE:
            self.winner = "You win!" if scorer is self.player else "Computer wins"

    def draw(self):
        rl.clear_background(BACKGROUND)
        for y in range(0, HEIGHT, 30):
            rl.draw_rectangle(WIDTH / 2 - 2, y + 8, 4, 14, DIM)
        centered(f"{self.player.score}   {self.computer.score}", 20, 48, FOREGROUND)
        self.player.draw()
        self.computer.draw()
        self.ball.draw()
        if self.winner:
            centered(self.winner, HEIGHT / 2 - 50, 40, FOREGROUND)
            centered("press space to play again", HEIGHT / 2 + 20, 20, DIM)
        elif not self.ball.moving:
            centered("press space to serve", HEIGHT - 60, 20, DIM)


def centered(text, y, size, color):
    rl.draw_text(text, (WIDTH - rl.measure_text(text, size)) / 2, y, size, color)


def main():
    rl.init_window(WIDTH, HEIGHT, "Small Python Pong")
    rl.set_target_fps(60)
    game = Game()
    while not rl.window_should_close():
        game.update(rl.get_frame_time())
        rl.begin_drawing()
        game.draw()
        rl.end_drawing()
    rl.close_window()


main()
