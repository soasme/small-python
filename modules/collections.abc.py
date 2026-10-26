"""Abstract base classes for containers, as CPython's collections.abc.

slim.py builds this submodule into the engine. As in CPython 3.15, it is the
standard library's _collections_abc module, which the host loader provides.
"""

import sys
import _collections_abc

sys.modules['collections.abc'] = _collections_abc
