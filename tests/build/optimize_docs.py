# build: -OO
# bundles: optimize_docs.py
# description: -OO also removes docstrings, keeping a future import first and an emptied body valid.
"""Module docstring."""
from __future__ import annotations


def f():
    "doc"


def g(): "only"


class C:
    """Class doc."""
    x = 1


def h():
    """doc"""; return 5


if __doc__ is not None:
    raise SystemExit("module docstring kept")
if (f.__doc__, g.__doc__, C.__doc__, h.__doc__) != (None, None, None, None):
    raise SystemExit("docstring kept")
if h() != 5 or C.x != 1:
    raise SystemExit("code removed")
assert False
