# spec: PLS-315 16.4.1, 16.4.2, 9.3.3
# description: Every store of a class body goes through its namespace,
# a __prepare__ mapping whose Python __setitem__, which may loop, sees
# each in order, the last statements' plain, augmented, unpacking and
# conditional stores and del included, with code compiled to "single"
# or "exec"; so do exec() locals.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
class LoggingDict(dict):
    def __setitem__(self, key, value):
        for _ in (): pass
        emit("d[%r] = %r" % (key, "line" if key == "__firstlineno__" else value))
        dict.__setitem__(self, key, value)
class Meta(type):
    @staticmethod
    def __prepare__(name, bases):
        return LoggingDict()
src = "class C(metaclass=Meta):\n    foo = 2+2\n    foo = 42\n    bar = 123\n"
exec(compile(src, "x", "single"), {"Meta": Meta, "__name__": "t"})
exec(compile(src, "x", "exec"), {"Meta": Meta, "__name__": "t"})
class D(metaclass=Meta):
    x = 1
    x += 2
    y, z = 3, 4
    if x: w = 5
    pass
    del y
exec("a = 1\nb = 2\nc = a", {}, LoggingDict())
EXPECTED = [
    "d['__module__'] = 't'",
    "d['__qualname__'] = 'C'",
    "d['__firstlineno__'] = 'line'",
    "d['foo'] = 4",
    "d['foo'] = 42",
    "d['bar'] = 123",
    "d['__static_attributes__'] = ()",
    "d['__module__'] = 't'",
    "d['__qualname__'] = 'C'",
    "d['__firstlineno__'] = 'line'",
    "d['foo'] = 4",
    "d['foo'] = 42",
    "d['bar'] = 123",
    "d['__static_attributes__'] = ()",
    "d['__module__'] = '__main__'",
    "d['__qualname__'] = 'D'",
    "d['__firstlineno__'] = 'line'",
    "d['x'] = 1",
    "d['x'] = 3",
    "d['y'] = 3",
    "d['z'] = 4",
    "d['w'] = 5",
    "d['__static_attributes__'] = ()",
    "d['a'] = 1",
    "d['b'] = 2",
    "d['c'] = 1",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
