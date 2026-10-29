"""Flappy Python: flap the python between the pipes.

flappy.c registers raylib; spyc bundles this file, the game package, its
themes, and the sprite into the program, so it needs no file at run time."""
import raylib as rl
from game import *
from game import sounds
from game.render import Renderer

FLAP_KEYS = (rl.KEY_SPACE, rl.KEY_UP, rl.KEY_W)


def flapped():
    return any(rl.is_key_pressed(key) for key in FLAP_KEYS) or rl.is_mouse_button_pressed(rl.MOUSE_BUTTON_LEFT)


def main():
    rl.init_window(tuning.WIDTH, tuning.HEIGHT, "Flappy Python")
    rl.set_target_fps(60)
    rl.init_audio_device()
    effects = {"flap": rl.load_sound(sounds.FLAP, sounds.RATE), "hit": rl.load_sound(sounds.HIT, sounds.RATE)}
    view = Renderer()
    world = World(seed=rl.get_random_value(1, 0x7FFFFFFF))
    while not rl.window_should_close():
        # A long frame (a dragged window) must not tunnel through a pipe.
        world.update(min(rl.get_frame_time(), 1 / 30), flapped())
        for event in world.events:
            rl.play_sound(effects[event])
        view.draw(world)
    rl.close_window()


main()
