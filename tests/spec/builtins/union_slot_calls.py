# spec: PLS-315 20.8.2, 29.5.1
# description: type's and a sentinel's __or__ and __ror__, as operators and
# called explicitly, bound, unbound or through map(), make the union of a
# class, None, a sentinel or a union with self, and return NotImplemented
# for any other operand, so a Python __ror__ or __or__ of the other side
# answers or a TypeError is raised; argument errors are TypeErrors; inside
# functions as at module level.
from harness import assert_eq
S = sentinel("S")
class R:
    def __ror__(self, o):
        for _ in (): pass
        return ('ror', o)
    def __or__(self, o): return ('or', o)
def run(f):
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    if type(r).__name__ == 'Union': r = ('Union', r.__args__)
    return r
cases = [lambda: S | 1, lambda: 1 | S, lambda: int | 1, lambda: 1 | int, lambda: S | 'a', lambda: int | None, lambda: S | (int | str),
         lambda: sentinel.__or__(S, 1), lambda: sentinel.__ror__(S, 1), lambda: type.__or__(int, 1), lambda: type.__ror__(int, 'x'),
         lambda: S | R(), lambda: int | R(), lambda: R() | S, lambda: S | [1], lambda: int | 2.5, lambda: S | S, lambda: sentinel.__or__(S, int),
         lambda: type.__or__(int, str), lambda: S | b'x', lambda: list[int] | S, lambda: S | list[int]]
more = [lambda: S.__or__(int), lambda: int.__or__(str), lambda: S.__ror__(int), lambda: list(map(int.__or__, [str])), lambda: type.__or__(int, other=str), lambda: S.__or__()]
EXPECTED = [
    '(\'TypeError\', "unsupported operand type(s) for |: \'sentinel\' and \'int\'")',
    '(\'TypeError\', "unsupported operand type(s) for |: \'int\' and \'sentinel\'")',
    '(\'TypeError\', "unsupported operand type(s) for |: \'type\' and \'int\'")',
    '(\'TypeError\', "unsupported operand type(s) for |: \'int\' and \'type\'")',
    '(\'TypeError\', "unsupported operand type(s) for |: \'sentinel\' and \'str\'")',
    "('Union', (<class 'int'>, <class 'NoneType'>))",
    "('Union', (S, <class 'int'>, <class 'str'>))",
    'NotImplemented',
    'NotImplemented',
    'NotImplemented',
    'NotImplemented',
    "('ror', S)",
    "('ror', <class 'int'>)",
    "('or', S)",
    '(\'TypeError\', "unsupported operand type(s) for |: \'sentinel\' and \'list\'")',
    '(\'TypeError\', "unsupported operand type(s) for |: \'type\' and \'float\'")',
    'S',
    "('Union', (S, <class 'int'>))",
    "('Union', (<class 'int'>, <class 'str'>))",
    '(\'TypeError\', "unsupported operand type(s) for |: \'sentinel\' and \'bytes\'")',
    "('Union', (list[int], S))",
    "('Union', (S, list[int]))",
    "('Union', (S, <class 'int'>))",
    '(\'TypeError\', "descriptor \'__or__\' requires a \'int\' object but received a \'type\'")',
    "('Union', (<class 'int'>, S))",
    '(\'TypeError\', "descriptor \'__or__\' requires a \'int\' object but received a \'type\'")',
    "('TypeError', 'wrapper __or__() takes no keyword arguments')",
    "('TypeError', 'expected 1 argument, got 0')",
]
all_cases = cases + more
assert_eq(len(all_cases), len(EXPECTED))
for i, (f, expected) in enumerate(zip(all_cases, EXPECTED)):
    assert_eq(repr(run(f)), expected, str(i))
def inside(): return [repr(run(f)) for f in all_cases]
assert_eq(inside(), EXPECTED)
# Whether an operand is a member is decided by its type: a __class__
# property is not read, and the slot declines.
class ClassProp:
    @property
    def __class__(self): raise KeyError("cls")
def class_property():
    return [type.__or__(int, ClassProp()), type.__ror__(int, ClassProp()), type.__or__(int, object())]
assert_eq(class_property(), [NotImplemented] * 3)
