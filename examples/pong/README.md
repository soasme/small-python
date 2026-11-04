# Pong

A [raylib](https://www.raylib.com/) game whose logic is Python. `pong.py`
holds the game; `raylib.c` is the `raylib` C module it imports. One `spyc`
command compiles both into the program, so `pong` runs anywhere without the
Python file.

## Run

Install raylib and pkg-config, then build and run from the repository root:

```sh
brew install raylib pkg-config    # Debian/Ubuntu: apt install libraylib-dev pkg-config
make -C examples/pong run
```

`make` builds `libspy.a` and `spyc` first if they are missing, then runs

```sh
spyc -o pong pong.py raylib.c -- $(pkg-config --cflags --libs raylib)
```

spyc embeds `pong.py`, compiles `raylib.c` as the module `raylib`, and
passes the arguments after `--` (raylib's headers and library) to the
compiler. Edit either file and run `make run` again to rebuild.

## Play

| Key | Action |
| --- | --- |
| W / S or Up / Down | Move your (left) paddle |
| Space | Serve, or start again after a game |
| Esc | Quit |

The first to 7 points wins against the computer.

## The `raylib` module

Numbers may be `int` or `float`; colors are `(r, g, b)` or `(r, g, b, a)`
tuples of integers in 0..255.

| Python | raylib |
| --- | --- |
| `init_window(w, h, title)` | `InitWindow` |
| `set_target_fps(fps)` | `SetTargetFPS` |
| `window_should_close()` | `WindowShouldClose` |
| `close_window()` | `CloseWindow` |
| `get_frame_time()` | `GetFrameTime` |
| `get_random_value(lo, hi)` | `GetRandomValue` |
| `is_key_down(key)`, `is_key_pressed(key)` | `IsKeyDown`, `IsKeyPressed` |
| `begin_drawing()`, `end_drawing()` | `BeginDrawing`, `EndDrawing` |
| `clear_background(color)` | `ClearBackground` |
| `draw_rectangle(x, y, w, h, color)` | `DrawRectangleRec` |
| `draw_circle(x, y, r, color)` | `DrawCircleV` |
| `draw_text(text, x, y, size, color)` | `DrawText` |
| `measure_text(text, size)` | `MeasureText` |

Key constants: `KEY_W`, `KEY_S`, `KEY_UP`, `KEY_DOWN`, `KEY_SPACE`.
To bind another function, write a wrapper in `raylib.c` and add it to
`functions`.
