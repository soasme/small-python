# spec: PLS-315 10.2.2, 27.1.1, 27.1.4
# description: keywords reaching a built-in's constructor through a subclass, and the lifetime of an iterator's subclass instance.
from harness import *

# tuple, float, frozenset, filter and reversed reject keywords in __new__
# unless the subclass replaces __init__, which then receives them.
for base, arg in ((tuple, [1]), (float, 1.5), (frozenset, [1]), (reversed, (1,))):
    class Plain(base):
        pass
    class WithInit(base):
        def __init__(self, arg, **keywords):
            self.keywords = keywords
    assert_raises(TypeError, base, arg, kw=1, message=f"{base.__name__}() takes no keyword arguments")
    assert_raises(TypeError, Plain, arg, kw=1, message=f"{base.__name__}() takes no keyword arguments")
    assert_eq(WithInit(arg, kw=1).keywords, {"kw": 1})
class Filtered(filter):
    def __init__(self, *args, **keywords):
        pass
assert_raises(TypeError, Filtered, kw=1, message="filter expected 2 arguments, got 0")

# list rejects keywords in __init__ unless the subclass replaces __new__.
class ListPlain(list):
    pass
class ListWithNew(list):
    def __new__(cls, arg, **keywords):
        return list.__new__(cls)
assert_raises(TypeError, ListPlain, [1], kw=1, message="list() takes no keyword arguments")
assert_eq(ListWithNew([1, 2], kw=1), [1, 2])

# A subclass of enumerate parses keywords as other built-ins do.
class Counted(enumerate):
    pass
assert_raises(TypeError, enumerate, [1], kw=1, message="'kw' is an invalid keyword argument for enumerate()")
assert_raises(TypeError, Counted, [1], kw=1, message="enumerate() got an unexpected keyword argument 'kw'")
assert_eq(list(Counted(iterable="ab", start=3)), [(3, "a"), (4, "b")])

# An iterator over a subclass instance holds the instance, which its
# reduction names, and releases it once exhausted.
for make in (iter, reversed):
    released = []
    class Held(tuple):
        def __del__(self):
            released.append(True)
    it = make(Held((1, 2)))
    assert_eq(released, [])
    assert_eq(type(it.__reduce__()[1][0]).__name__, "Held")
    assert_eq(len(list(it)), 2)
    assert_eq(released, [True])

# Repeating an exact tuple, str or bytes into an equal value, and tuple()
# or float() of an exact value, give the value itself.
for value in ((1, 2), "ab", b"ab"):
    assert_is(value * 1, value)
    assert_is(1 * value, value)
    empty = value[:0]
    assert_is(empty * 5, empty)
point = (1, 2)
assert_is(tuple(point), point)
half = 0.5
assert_is(float(half), half)
