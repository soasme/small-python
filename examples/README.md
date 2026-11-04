# Examples

Programs that run on Small Python, from one-line scripts to games and a web
application. Run the scripts with `spy` from the repository root after
`make`; each larger example has a README with its own build steps.

## Scripts

| Example | Shows |
| --- | --- |
| [`hello.py`](hello.py) | Printing: `./spy examples/hello.py` |
| [`fibonacci.py`](fibonacci.py) | A recursive function |
| [`closures.py`](closures.py) | A closure, and a list that contains itself |
| [`generators.py`](generators.py) | `send`, `yield from` with a return value, and `finally` on close |
| [`embed.c`](embed.c) | Embedding the engine in C: define a function, evaluate, handle errors |
| [`fib.c`](fib.c) | A native module: `make examples/fib.so`, then `./spy examples/test_fib.py` imports it |

## Applications

| Example | Shows |
| --- | --- |
| [`pong`](pong) | A raylib game whose logic is Python, calling a `raylib` module the host registers with `spy_new_module` |
| [`flappy`](flappy) | `spyc` bundling a game package, dynamically imported themes and a sprite into one executable with a static raylib |
| [`todo`](todo) | A Flask-style Python application served by a Rust host through the `small-python` crate |
| [`jsonify`](jsonify) | A JSON pretty-printer whose `json` module is Rust on serde_json, linked by `spyc` as `libjson.a` |

## Elsewhere

[Small Craft](https://github.com/soasme/small-craft) is a block-building
sandbox in a repository of its own: endless generated terrain, building and
lights, flying and builder commands, with every vertex and matrix computed in
Python and drawn by raylib through custom shaders. It vendors the engine and
builds two ways: one native executable bundled by `spyc`, and a WebGL 2 build
by Emscripten that is published as a static site and plays in a page or an X
player card ([play it](https://www.soasme.com/small-craft/)).
