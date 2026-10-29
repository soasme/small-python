# Pong

A [raylib](https://www.raylib.com/) game whose logic is Python. `pong.py`
holds the game; `pong.c` is the host. It registers a `raylib` C module with
`spy_new_module`, as a QuickJS host registers one with `JS_NewCModule`, then
runs the script.

## Run

Install raylib and pkg-config, then build and run from the repository root:

```sh
brew install raylib pkg-config    # Debian/Ubuntu: apt install libraylib-dev pkg-config
make -C examples/pong run
```

`make` builds `libspy.a` first if it is missing. To run a different script
on the same host, pass it: `examples/pong/pong path/to/game.py`.

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
To bind another function, write a wrapper in `pong.c` and add it to
`functions`.
