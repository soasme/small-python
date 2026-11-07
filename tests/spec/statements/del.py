# spec: PLS-315 14.7
# description: del of names, subscripts, attributes, and in loops; a
# subscript's deletion calls its object's __delitem__ with the key, in
# target order, and an object without one raises TypeError.
from harness import *

a = 1
del a

class MyObject: pass
foo = MyObject()
foo.bar = 2
assert hasattr(foo, 'bar')
del foo.bar

assert not hasattr(foo, 'bar')

x = 1
y = 2
del (x, y)
assert_raises(NameError, lambda: x)  # noqa: F821
assert_raises(NameError, lambda: y)  # noqa: F821

with assert_raises(NameError):
    del y  # noqa: F821


class MyTest:
    def __del__(self):
        type(self)()

def test_del_panic():
    mytest = MyTest()
    del mytest


def f():
    del b # noqa

b = 'a'
assert_raises(UnboundLocalError, f)

deleted = []
class Deleting:
    def __init__(self): self.items = {1: "a", 3: "b"}
    def __delitem__(self, key):
        for _ in range(2): pass
        deleted.append(key)
        del self.items[key]
class Plain: pass
def deletions():
    d = Deleting(); holder = [d]
    del d[1]
    del holder[0][3], d.items
    try:
        del Plain()[0]
    except TypeError as e:
        deleted.append(str(e))
    try:
        del d[5]
    except AttributeError as e:
        deleted.append(str(e))
    numbers = [0, 1, 2]
    del numbers[0], numbers[-1]
    return deleted, d.__dict__, numbers
assert_eq(deletions(), ([1, 3, "'Plain' object doesn't support item deletion", 5,
                         "'Deleting' object has no attribute 'items'"], {}, [1]))
