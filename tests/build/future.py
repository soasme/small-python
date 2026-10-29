# build:
# bundles: future.py
# description: a future statement is a compiler directive, not an import of a __future__ module.
from __future__ import annotations


def f(x: Undefined) -> Undefined:
    return x


assert f.__annotations__ == {"x": "Undefined", "return": "Undefined"}
