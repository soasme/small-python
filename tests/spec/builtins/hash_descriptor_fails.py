# spec: PLS-315 7.5.7, 7.3.2, 26.1
# description: Hash looks __hash__ up by LookupSpecialMaybe: a descriptor
# whose __get__ raises AttributeError leaves the object unhashable, which
# a dict and a set then name as their key or element, while any other
# exception from __get__ propagates.
from harness import assert_eq

class Gone:
    def __get__(self, obj, owner=None):
        for _ in (): pass
        raise AttributeError("no hash")

class K:
    __hash__ = Gone()

class Raises:
    def __get__(self, obj, owner=None): raise KeyError("r")

class L:
    __hash__ = Raises()

def attempt(f):
    try: return f()
    except Exception as e: return type(e).__name__, str(e)

assert_eq([attempt(lambda: hash(K())), attempt(lambda: {K(): 1}), attempt(lambda: {K()}),
           attempt(lambda: K() in {1: 2}), attempt(lambda: hash(L()))],
          [("TypeError", "unhashable type: 'K'"), ("TypeError", "cannot use 'K' as a dict key (unhashable type: 'K')"),
           ("TypeError", "cannot use 'K' as a set element (unhashable type: 'K')"),
           ("TypeError", "cannot use 'K' as a dict key (unhashable type: 'K')"), ("KeyError", "'r'")])
