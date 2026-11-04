"""jsonify FILE: print a JSON file indented by two spaces, in color.

The json module is Rust (src/lib.rs, on serde_json); spyc links it into
this program as libjson.a. Reading the file and coloring are Python.
"""

import json
import sys

KEY, STRING, NUMBER, CONSTANT, RESET = "\033[1;34m", "\033[32m", "\033[36m", "\033[35m", "\033[0m"


def paint(value, color):
    return color + json.dumps(value, ensure_ascii=False) + RESET


def render(value, depth=0):
    """Yield the text of value as json.dumps(value, indent=2) spells it,
    with keys, strings, numbers and constants in color."""
    inner, outer = "\n" + "  " * (depth + 1), "\n" + "  " * depth
    if isinstance(value, dict) and value:
        yield "{"
        for i, (key, item) in enumerate(value.items()):
            yield ("," if i else "") + inner + paint(key, KEY) + ": "
            yield from render(item, depth + 1)
        yield outer + "}"
    elif isinstance(value, list) and value:
        yield "["
        for i, item in enumerate(value):
            yield ("," if i else "") + inner
            yield from render(item, depth + 1)
        yield outer + "]"
    elif isinstance(value, (dict, list)):
        yield json.dumps(value)
    elif value is None or isinstance(value, bool):
        yield paint(value, CONSTANT)
    else:
        yield paint(value, STRING if isinstance(value, str) else NUMBER)


if len(sys.argv) != 2:
    raise SystemExit("usage: jsonify FILE")
with open(sys.argv[1], encoding="utf-8") as file:
    document = json.load(file)
print("".join(render(document)))
