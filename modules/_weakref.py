"""Weak-reference support module.

Small Python's standard layer (spy-std.c) provides this module as the primitive half of weakref,
following CPython's _weakref. Its names are the weakref module's own objects.
"""

from weakref import (ref, proxy, getweakrefcount, getweakrefs, ReferenceType, ProxyType,
                     CallableProxyType, _remove_dead_weakref)
