# spec: PLS-315 14.7, 7.8.2, 7.8.3, 13.10
# description: Inside a generator, deleting an item whose key yields
# deletes it from a dictionary or list at once and raises TypeError for an
# instance whose class defines no item methods; inside a function, `in`
# over an instance whose Python __iter__ raises TypeError, with no
# __contains__, raises TypeError naming the instance's type.
from harness import *

class Plain:
    pass

class Refusing:
    def __iter__(self):
        for _ in range(2): pass
        raise TypeError("no items")

def remove(target):
    try:
        del target[(yield)]
    except TypeError as e:
        yield str(e)
    yield target

def deleted(target, key):
    g = remove(target)
    next(g)
    return g.send(key)

def search():
    try:
        return 1 in Refusing()
    except TypeError as e:
        return str(e)

assert_eq([deleted({"a": 1, "b": 2}, "a"), deleted([1, 2, 3], 0), deleted(Plain(), 0), search()],
          [{"b": 2}, [2, 3], "'Plain' object doesn't support item deletion",
           "argument of type 'Refusing' is not a container or iterable"])
