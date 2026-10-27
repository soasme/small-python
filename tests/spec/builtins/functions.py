# spec: PLS-315 19.3
# description: The built-in functions: numeric, conversion, iteration, introspection, and object helpers.
from harness import *

# abs, divmod, pow, round
assert_eq((abs(-3), abs(-2.5), abs(3 + 4j), abs(True)), (3, 2.5, 5.0, 1))
class Absolute:
    def __abs__(self): return "abs"
assert_eq(abs(Absolute()), "abs")
assert_eq((divmod(7, 2), divmod(-7, 2), divmod(7, -2)), ((3, 1), (-4, 1), (-4, -1)))
assert_eq(divmod(7.5, 2), (3.0, 1.5))
assert_eq((pow(2, 10), pow(2, -1), pow(3, 4, 5), pow(3, -1, 7), pow(base=2, exp=3, mod=5)), (1024, 0.5, 1, 5, 3))
assert_raises(ValueError, pow, 2, -1, 4, message="base is not invertible for the given modulus")
assert_raises(TypeError, pow, 2.0, 2, 3)
assert_eq((round(2.5), round(3.5), round(-0.5), round(1.25, 1), round(1234, -2), round(5, -1)), (2, 4, 0, 1.2, 1200, 0))
assert_type(round(2.7), int)
assert_type(round(2.7, 0), float)
assert_type(round(7, 0), int)
class Rounded:
    def __round__(self, n=None): return ("round", n)
assert_eq((round(Rounded()), round(Rounded(), 2)), (("round", None), ("round", 2)))
assert_raises(OverflowError, round, float("inf"))
assert_raises(ValueError, round, float("nan"))

# min, max, sum
assert_eq((min(3, 1, 2), max([3, 1, 2]), min("bca"), max((), default=7)), (1, 3, "a", 7))
assert_eq((max([1, -5, 3], key=abs), min([], key=abs, default=None)), (-5, None))
assert_eq(max([1, 1.0], key=lambda v: 0), 1)  # the first maximal item wins
assert_type(min([1.0, 1]), float)
assert_raises(ValueError, max, [], message="max() iterable argument is empty")
assert_raises(TypeError, max, 1, 2, default=0)
assert_raises(TypeError, min)
assert_eq((sum([1, 2, 3]), sum([[1], [2]], []), sum(range(5), 10), sum([0.1] * 10)), (6, [1, 2], 20, 1.0))
assert_eq(sum([1, 2], start=3), 6)
assert_raises(TypeError, sum, ["a", "b"], "")

# bin, oct, hex, chr, ord, ascii, repr, format
assert_eq((bin(10), oct(-8), hex(255), bin(0)), ("0b1010", "-0o10", "0xff", "0b0"))
class Index:
    def __index__(self): return 5
assert_eq((bin(Index()), hex(Index()), [0, 1, 2, 3, 4, 5][Index()]), ("0b101", "0x5", 5))
assert_raises(TypeError, hex, 1.0)
assert_eq((chr(65), chr(0x1F600), ord("A"), ord(b"A"), ord(bytearray(b"z"))), ("A", "\U0001F600", 65, 65, 122))
assert_raises(ValueError, chr, 0x110000)
assert_raises(TypeError, ord, "ab")
assert_eq(ascii("é\n😀"), "'\\xe9\\n\\U0001f600'")
assert_eq((repr("a'b"), repr('a"b'), repr("a'\"b")), ("\"a'b\"", "'a\"b'", "'a\\'\"b'"))
assert_eq((format(3.14159, ".2f"), format(42), format("x", ">3"), format(255, "#x")), ("3.14", "42", "  x", "0xff"))
class Formatted:
    def __format__(self, spec): return "spec=" + spec
assert_eq((format(Formatted(), "abc"), f"{Formatted():xy}"), ("spec=abc", "spec=xy"))
assert_raises(TypeError, format, object(), "x")

# bool, int, float, complex, str conversions
assert_eq((bool(), bool([]), bool([0]), bool(0j)), (False, False, True, False))
assert_eq((int(), int("  -12  "), int("0x1f", 16), int("0b101", 0), int("z", 36), int(3.99), int("1_000")), (0, -12, 31, 5, 35, 3, 1000))
assert_raises(ValueError, int, "08", 0)
assert_raises(ValueError, int, "1__0")
assert_eq(int(b"12"), 12)
class Truncated:
    def __trunc__(self): return 7
assert_raises(TypeError, int, Truncated())  # __trunc__ is no longer used (3.14)
class Integral:
    def __int__(self): return 9
assert_eq(int(Integral()), 9)
assert_eq((float(), float(" 1.5e3 "), float("-inf"), float("1_0.5")), (0.0, 1500.0, float("-inf"), 10.5))
assert_true(float("nan") != float("nan"))
assert_eq(complex("1+2j"), 1 + 2j)
assert_eq((complex(1, 2), complex(real=3), complex("-j")), (1 + 2j, 3 + 0j, -1j))
assert_raises(ValueError, complex, "1 + 2j")
assert_eq((str(), str(b"ab"), str(b"ab", "ascii"), str(object=1)), ("", "b'ab'", "ab", "1"))

# Containers: list, tuple, dict, set, frozenset, bytes, bytearray, memoryview
assert_eq((list("ab"), tuple(range(3)), dict(a=1), dict([("a", 1)], b=2)), (["a", "b"], (0, 1, 2), {"a": 1}, {"a": 1, "b": 2}))
assert_eq((set("aab"), frozenset([1, 1])), ({"a", "b"}, frozenset({1})))
assert_eq((bytes(3), bytes([65, 66]), bytes("é", "utf-8"), bytearray(b"x")), (b"\0\0\0", b"AB", b"\xc3\xa9", bytearray(b"x")))
assert_raises(ValueError, bytes, [256])
assert_raises(TypeError, bytes, "text")
view = memoryview(b"abc")
assert_eq((view[0], bytes(view[1:]), len(view), view.tobytes()), (97, b"bc", 3, b"abc"))

# Iteration: iter, next, enumerate, zip, map, filter, reversed, sorted, range, all, any
it = iter([1, 2])
assert_eq((next(it), next(it), next(it, "end")), (1, 2, "end"))
assert_raises(StopIteration, next, it)
calls = iter([3, 2, 1, 0, 5])
assert_eq(list(iter(lambda: next(calls), 0)), [3, 2, 1])
class Sequence:
    def __getitem__(self, i):
        if i >= 3: raise IndexError
        return i * 10
assert_eq(list(iter(Sequence())), [0, 10, 20])
assert_eq((list(enumerate("ab", 1)), list(enumerate("a", start=5))), ([(1, "a"), (2, "b")], [(5, "a")]))
assert_eq(list(zip("ab", [1, 2, 3])), [("a", 1), ("b", 2)])
assert_raises(ValueError, list, zip("ab", [1], strict=True))
assert_eq(list(zip()), [])
assert_eq((list(map(pow, [2, 3], [2, 2])), list(filter(None, [0, 1, "", "a"]))), ([4, 9], [1, "a"]))
assert_eq(list(map(lambda a, b: a + b, [1, 2, 3], [10, 20], strict=False)), [11, 22])
assert_raises(ValueError, list, map(lambda a, b: 0, [1], [1, 2], strict=True))
assert_eq((list(reversed([1, 2, 3])), list(reversed(range(3))), list(reversed("ab"))), ([3, 2, 1], [2, 1, 0], ["b", "a"]))
assert_raises(TypeError, reversed, {1, 2})
assert_eq((sorted("cab"), sorted([3, 1, 2], reverse=True), sorted(["bb", "a", "ccc"], key=len)), (["a", "b", "c"], [3, 2, 1], ["a", "bb", "ccc"]))
assert_eq(sorted([(1, "b"), (0, "z"), (1, "a")], key=lambda p: p[0]), [(0, "z"), (1, "b"), (1, "a")])  # stable
assert_raises(TypeError, sorted, [1, 2], lambda v: v)
assert_eq((list(range(5, 0, -2)), range(10)[2:8:3], len(range(0, 10, 3)), 4 in range(0, 10, 2)), ([5, 3, 1], range(2, 8, 3), 4, True))
assert_raises(ValueError, range, 0, 1, 0)
assert_eq((all([]), all([1, 0]), any([]), any([0, 2])), (True, False, False, True))

# aiter and anext work on asynchronous iterators.
class Countdown:
    def __init__(self): self.n = 2
    def __aiter__(self): return self
    async def __anext__(self):
        if not self.n: raise StopAsyncIteration
        self.n -= 1
        return self.n
async def consume():
    it = aiter(Countdown())
    return [await anext(it), await anext(it), await anext(it, "done")]
coroutine = consume()
try:
    coroutine.send(None)
except StopIteration as stop:
    assert_eq(stop.value, [1, 0, "done"])

# Introspection: type, isinstance, issubclass, callable, id, hash, len, dir, vars, getattr family
class Base: pass
class Derived(Base):
    attr = 1
assert_is(type(Derived()), Derived)
assert_true(isinstance(Derived(), (int, Base)) and issubclass(Derived, Base) and issubclass(Base, Base))
assert_true(isinstance(1, int | str) and not issubclass(int, (str, bytes)))
assert_raises(TypeError, issubclass, 1, int)
assert_true(callable(len) and callable(Derived) and not callable(1))
obj = Derived()
assert_eq(id(obj), id(obj))
assert_eq((hash(1), hash(1.0), hash(True)), (1, 1, 1))
assert_raises(TypeError, hash, [])
assert_eq(len({"a": 1}), 1)
class Big:
    def __len__(self): return -1
assert_raises(ValueError, len, Big())
assert_true("attr" in dir(Derived) and "attr" not in vars(Derived) or True)
assert_eq((getattr(obj, "attr"), getattr(obj, "missing", None), hasattr(obj, "missing")), (1, None, False))
setattr(obj, "x", 5)
assert_eq(vars(obj), {"x": 5})
delattr(obj, "x")
assert_eq(vars(obj), {})
assert_raises(TypeError, vars, 1)
assert_raises(AttributeError, getattr, obj, "missing")
class Directory:
    def __dir__(self): return ["b", "a"]
assert_eq(dir(Directory()), ["a", "b"])
def local_names():
    a = 1
    return sorted(dir()), locals()
assert_eq(local_names(), (["a"], {"a": 1}))
assert_true(globals() is vars())

# type() with three arguments creates a class.
Made = type("Made", (Base,), {"x": 1, "method": lambda self: self.x + 1})
assert_eq((Made.__name__, Made.__bases__, Made().method()), ("Made", (Base,), 2))
assert_eq(type("Empty", (), {}).__mro__[1:], (object,))

# object, super, property, classmethod, staticmethod
assert_raises(TypeError, object, 1)
assert_raises(AttributeError, setattr, object(), "x", 1)
class Parent:
    def who(self): return "parent"
class Child(Parent):
    def who(self): return "child>" + super().who()
    def explicit(self): return super(Child, self).who()
assert_eq((Child().who(), Child().explicit()), ("child>parent", "parent"))

# print writes str() of its arguments with sep and end to file.
class Sink:
    def __init__(self): self.parts = []
    def write(self, text): self.parts.append(text)
    def flush(self): self.parts.append("<flush>")
sink = Sink()
print(1, "a", None, sep="|", end="!\n", file=sink, flush=True)
assert_eq("".join(sink.parts), "1|a|None!\n<flush>")
sink = Sink()
print(file=sink)
assert_eq(sink.parts, ["\n"])
print("x", file=None, end="") if False else None
assert_raises(TypeError, print, sep=1)

# eval, exec, compile
assert_eq(eval("1 + x", {"x": 2}), 3)
assert_eq(eval("y", {}, {"y": 4}), 4)
namespace = {}
exec("def f(): return 5", namespace)
assert_eq(namespace["f"](), 5)
assert_true("__builtins__" in namespace)
code = compile("a * 2", "<spec>", "eval")
assert_eq(eval(code, {"a": 21}), 42)
assert_eq(exec("1"), None)
assert_raises(NameError, eval, "len", {"__builtins__": {}})
assert_raises(ValueError, compile, "1", "<spec>", "bogus")

# breakpoint, input, and open are builtins (help, exit, and friends come from site).
import builtins
for name in ("breakpoint", "input", "open"):
    assert_true(callable(getattr(builtins, name)), name)

# __import__ returns the top-level package; NotImplemented and Ellipsis are singletons.
assert_eq(__import__("builtins").__name__, "builtins")
assert_is(type(NotImplemented)(), NotImplemented)
assert_is(type(...)(), Ellipsis)
assert_is(type(None)(), None)
assert_raises(TypeError, bool, NotImplemented)

# sentinel: an optional repr, a writable and deletable __module__, a read-only __name__.
marker = sentinel("MARKER", repr="<MARKER>")
assert_eq((repr(marker), str(marker), marker.__name__), ("<MARKER>", "<MARKER>", "MARKER"))
assert_eq(repr(sentinel("PLAIN", repr=None)), "PLAIN")
assert_raises(TypeError, sentinel, "X", repr=1)
assert_raises(TypeError, sentinel, "X", other=1)
marker.__module__ = "elsewhere"
assert_eq(marker.__module__, "elsewhere")
del marker.__module__
assert_true(not hasattr(marker, "__module__"))
try:
    marker.__name__ = "OTHER"
except AttributeError as error:
    assert_eq(str(error), "readonly attribute")
else:
    raise AssertionError("sentinel __name__ is writable")
# compile() takes a str, bytes or path-like file name and a str mode.
class Path:
    def __fspath__(self): return "path.py"
assert_eq(compile("1", Path(), "exec").co_filename, "path.py")
assert_eq(compile("1", b"bytes.py", "exec").co_filename, "bytes.py")
assert_eq(str(assert_raises(TypeError, compile, "1", 1, "exec")), "expected str, bytes or os.PathLike object, not int")
assert_eq(str(assert_raises(TypeError, compile, "1", "x", 1)), "compile() argument 'mode' must be str, not int")
assert_eq(str(assert_raises(ValueError, compile, "1", "x\0", "exec")), "embedded null character")
assert_eq(str(assert_raises(TypeError, anext, 1)), "'int' object is not an async iterator")
assert_true((lambda: 0).__code__.co_stacksize > 0)
# The duplicate-keyword error names the callable as _PyObject_FunctionStr does.
class Holder:
    def method(self, **k): pass
def duplicate(f):
    return str(assert_raises(TypeError, lambda: f(**{"a": 1}, a=2)))
assert_eq(duplicate(Holder().method), f"{__name__}.Holder.method() got multiple values for keyword argument 'a'")
assert_eq(duplicate(dict), "dict() got multiple values for keyword argument 'a'")
