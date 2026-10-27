# spec: library/stdtypes.html
# description: Methods and operations of the built-in types: numbers, str, bytes, list, tuple, dict, set, range.
from harness import *

# int
assert_eq(((255).bit_length(), (-1).bit_length(), (0b1011).bit_count(), (-5).bit_count()), (8, 1, 3, 2))
assert_eq(((1024).to_bytes(2, "big"), (1).to_bytes(2, "little"), (-1).to_bytes(1, signed=True)), (b"\x04\x00", b"\x01\x00", b"\xff"))
assert_eq((int.from_bytes(b"\x00\x10", "big"), int.from_bytes(b"\xff", signed=True), int.from_bytes([1, 0], "little")), (16, -1, 1))
assert_raises(OverflowError, (256).to_bytes, 1)
assert_eq(((6).as_integer_ratio(), (5).conjugate(), (5).real, (5).imag, (5).numerator, (5).denominator), ((6, 1), 5, 5, 0, 5, 1))
assert_true((7).is_integer())
assert_eq((-7 // 2, -7 % 2, 7 // -2, 2 ** 100 // 3 ** 40 > 0), (-4, 1, -4, True))
assert_eq((~5, 1 << 70 >> 69, -8 >> 1, 6 & 3, 6 | 3, 6 ^ 3), (-6, 2, -4, 2, 7, 5))
assert_raises(ValueError, lambda: 1 << -1)

# float
assert_eq(((2.5).as_integer_ratio(), (0.5).hex(), float.fromhex("0x1.8p1"), (3.0).is_integer()), ((5, 2), "0x1.0000000000000p-1", 3.0, True))
assert_eq((repr(0.1), repr(1e16), repr(1e-5), repr(-0.0), str(1.0), repr(1e22)), ("0.1", "1e+16", "1e-05", "-0.0", "1.0", "1e+22"))
assert_eq((float("inf") > 1e308, float("nan") == float("nan"), -0.0 == 0.0), (True, False, True))
assert_eq((7.5 // 2, -7.5 % 2, divmod(-7.5, 2), 2.0 ** -1), (3.0, 0.5, (-4.0, 0.5), 0.5))
assert_raises(ZeroDivisionError, lambda: 1.0 / 0)
assert_raises(OverflowError, lambda: 10.0 ** 400)
assert_eq((round(0.125, 2), round(0.375, 2), 0.1 + 0.2 == 0.3, 1e308 * 10), (0.12, 0.38, False, float("inf")))
assert_eq(float.from_number(3), 3.0)
assert_raises(TypeError, float.from_number, "3")

# complex
z = 3 + 4j
assert_eq((z.real, z.imag, z.conjugate(), abs(z), z * 1j, (1 + 1j) ** 2), (3.0, 4.0, 3 - 4j, 5.0, -4 + 3j, 2j))
assert_eq((repr(1j), repr(-1j), repr(complex(1, -0.0)), repr(complex(-0.0, 1))), ("1j", "(-0-1j)", "(1-0j)", "(-0+1j)"))
assert_raises(TypeError, lambda: 1j < 2j)
assert_raises(TypeError, lambda: 1j // 1)

# bool is a subclass of int
assert_eq((True + True, True * 3, True & False, True | False, repr(True ^ True)), (2, 3, False, True, "False"))
assert_eq((isinstance(True, int), str(int(True)), str(True), f"{True:d}"), (True, "1", "True", "1"))

# str
s = "Hello, World"
assert_eq((s.lower(), s.upper(), s.swapcase(), "hello world".title(), "hELLO".capitalize(), "Straße".casefold()),
          ("hello, world", "HELLO, WORLD", "hELLO, wORLD", "Hello World", "Hello", "strasse"))
assert_eq((s.find("o"), s.rfind("o"), s.find("z"), s.index("W"), s.count("l"), s.count(""), s.find("o", 5, 9)), (4, 8, -1, 7, 3, 13, 8))
assert_raises(ValueError, s.index, "z", message="substring not found")
assert_eq((s.startswith("He"), s.startswith(("x", "Hel")), s.endswith("ld", 0, 12), s.startswith("W", 7)), (True, True, True, True))
assert_eq((" a b ".split(), "a,b,,c".split(","), "a b c".split(None, 1), "a b c".rsplit(None, 1), "".split(), "".split(",")),
          (["a", "b"], ["a", "b", "", "c"], ["a", "b c"], ["a b", "c"], [], [""]))
assert_eq(("a\nb\r\nc\rd".splitlines(), "a\nb\n".splitlines(True), "x\x0by\x1cz".splitlines()), (["a", "b", "c", "d"], ["a\n", "b\n"], ["x", "y", "z"]))
assert_eq(("a-b-c".partition("-"), "a-b-c".rpartition("-"), "abc".partition("x")), (("a", "-", "b-c"), ("a-b", "-", "c"), ("abc", "", "")))
assert_eq(("  x  ".strip(), "xxaxx".strip("x"), "  x".lstrip(), "x  ".rstrip(), "abcab".removeprefix("ab"), "abcab".removesuffix("ab")), ("x", "a", "x", "x", "cab", "abc"))
assert_eq(("-".join(["a", "b"]), "aaa".replace("a", "b", 2), "abc".replace("", "-"), "a\tb".expandtabs(4)), ("a-b", "bba", "-a-b-c-", "a   b"))
assert_raises(TypeError, "".join, ["a", 1])
assert_eq(("ab".center(6, "*"), "ab".ljust(4), "ab".rjust(4, "0"), "42".zfill(5), "-42".zfill(5), "+x".zfill(4)), ("**ab**", "ab  ", "00ab", "00042", "-0042", "+00x"))
assert_eq(("abc".isalpha(), "a1".isalnum(), "123".isdigit(), "²".isdigit(), "²".isdecimal(), "½".isnumeric(), " \t".isspace(), "Ab Cd".istitle(), "ab".islower(), "AB".isupper(), "_a1".isidentifier(), "\x7f".isprintable(), "abc".isascii()),
          (True, True, True, True, False, True, True, True, True, True, True, False, True))
assert_eq(("".isalpha(), "".isspace(), "1".isidentifier(), "class".isidentifier()), (False, False, False, True))
table = str.maketrans("ab", "xy", "c")
assert_eq(("abcabc".translate(table), str.maketrans({"a": "1"}), "abc".translate({97: None, 98: "BB"})), ("xyxy", {97: "1"}, "BBc"))
assert_eq(("{} {}".format(1, 2), "{1}{0}".format("a", "b"), "{x[0]}{y.real}".format(x=[5], y=3), "{:>5}|{:^5}|{:<5}".format(1, 2, 3)), ("1 2", "ba", "53", "    1|  2  |3    "))
assert_eq(("{0!r:>6}".format("a"), "{:,}".format(1234567), "{:_b}".format(255), "{:.3}".format(3.14159), "{:e}".format(12345.678), "{:%}".format(0.25)),
          ("   'a'", "1,234,567", "1111_1111", "3.14", "1.234568e+04", "25.000000%"))
assert_eq("{a}-{b}".format_map({"a": 1, "b": 2}), "1-2")
assert_raises(KeyError, "{missing}".format)
assert_raises(IndexError, "{1}".format, 0)
assert_raises(ValueError, "{} {0}".format, 1, 2)
assert_eq(("%s %r %d %5.2f %x %o %c %%" % ("a", "b", 42, 3.14159, 255, 8, 65), "%(n)s" % {"n": 1}, "%-4d|" % 7, "%+d" % 5, "%05.1f" % 2.25),
          ("a 'b' 42  3.14 ff 10 A %", "1", "7   |", "+5", "002.2"))
assert_raises(TypeError, lambda: "%d" % "x")
assert_raises(TypeError, lambda: "%s %s" % (1,))
assert_eq(("é".encode(), "é".encode("latin-1"), "€".encode("utf-8"), "ab".encode("ascii")), (b"\xc3\xa9", b"\xe9", b"\xe2\x82\xac", b"ab"))
assert_raises(UnicodeEncodeError, "é".encode, "ascii")
assert_eq(("é".encode("ascii", "replace"), "é".encode("ascii", "ignore"), "é".encode("ascii", "backslashreplace"), "é".encode("ascii", "xmlcharrefreplace")), (b"?", b"", b"\\xe9", b"&#233;"))
assert_eq((s[::-1], s[-5:], s[100:], s[1:10:3], len("😀"), "😀"[0], "abc" * 2, 2 * "ab", "b" in "abc", "" in "abc"),
          ("dlroW ,olleH", "World", "", "eoW", 1, "😀", "abcabc", "abab", True, True))
assert_eq(("a" < "b", "abc" < "abd", "Z" < "a", "a" < "aa", "é" > "z"), (True, True, True, True, True))
assert_raises(TypeError, lambda: "a" < 1)
assert_raises(TypeError, lambda: "a" + 1)
def assign_char(): s[0] = "x"
assert_raises(TypeError, assign_char)

# bytes and bytearray
b = b"Hello"
assert_eq((b[0], b[-1:], b.lower(), b.upper(), b.find(b"l"), b.count(b"l"), b.replace(b"l", b"L"), b.split(b"e"), b.hex(), b.hex(":", 2)),
          (72, b"o", b"hello", b"HELLO", 2, 2, b"HeLLo", [b"H", b"llo"], "48656c6c6f", "48:656c:6c6f"))
assert_eq((bytes.fromhex("de ad"), b"a,b".partition(b","), b" x ".strip(), b"ab".center(4), b"%d-%s" % (1, b"x"), b"a" * 3, b"ab".decode()),
          (b"\xde\xad", (b"a", b",", b"b"), b"x", b" ab ", b"1-x", b"aaa", "ab"))
assert_eq((b"abc".startswith(b"ab"), b"x".isalpha(), b"1".isdigit(), b"a b".title(), b"\xff".decode("latin-1"), b"\xff".decode("utf-8", "replace")), (True, True, True, b"A B", "\xff", "�"))
assert_raises(UnicodeDecodeError, b"\xff".decode)
assert_raises(TypeError, lambda: b"a" + "a")
assert_true(b"a" != "a")
assert_eq((65 in b"A", b"B" in b"ABC"), (True, True))
ba = bytearray(b"abc")
ba[0] = 120
ba += b"d"
ba.append(101)
ba.extend([102])
ba[1:3] = b"YZW"
del ba[0]
assert_eq((ba.pop(), ba.find(b"W"), bytes(ba)), (102, 2, b"YZWde"))
ba.insert(0, 33); ba.remove(87); ba.reverse()
assert_eq(ba, bytearray(b"edZY!"))
assert_raises(ValueError, ba.append, 256)
assert_raises(TypeError, hash, ba)

# list
items = [3, 1, 2]
items.append(4); items.extend((5, 6)); items.insert(0, 0); items.insert(100, 7); items.insert(-100, -1)
assert_eq(items, [-1, 0, 3, 1, 2, 4, 5, 6, 7])
assert_eq((items.pop(), items.pop(0), items.index(4), items.count(3)), (7, -1, 4, 1))
items.remove(3); items.reverse()
assert_eq(items, [6, 5, 4, 2, 1, 0])
items.sort(); items.sort(key=lambda v: -v); copied = items.copy(); items.clear()
assert_eq((items, copied), ([], [6, 5, 4, 2, 1, 0]))
assert_raises(ValueError, [1].remove, 2)
assert_raises(IndexError, [].pop)
assert_raises(ValueError, [1, 2].index, 1, 1)
grid = [[0] * 2] * 2
grid[0][0] = 1
assert_eq(grid, [[1, 0], [1, 0]])
nums = list(range(10))
nums[2:5] = ["a"]
nums[::3] = "xyz"
del nums[1::2]
assert_eq(nums, ["x", "a", 6, "z"])
assert_raises(ValueError, nums.__setitem__, slice(None, None, 2), [1])
assert_eq(([1, 2] < [1, 3], [1, 2] < [1, 2, 0], [1] == [1.0], [] < [0]), (True, True, True, True))
# Sorting compares with < only and is stable; a key error propagates.
class Item:
    def __init__(self, v): self.v = v
    def __lt__(self, other): return self.v < other.v
assert_eq([i.v for i in sorted([Item(2), Item(1)])], [1, 2])
with_errors = [3, 1, "a"]
assert_raises(TypeError, with_errors.sort)
mutating = [3, 2, 1]
def mutate(v):
    mutating.append(0)
    return v
assert_raises(ValueError, mutating.sort, key=mutate)

# tuple
t = (1, 2, 2, 3)
assert_eq((t.count(2), t.index(3), t[1:3], t + (4,), t * 0, (1,) * 2, (1, 2) < (1, 2, 3), hash((1, 2)) == hash((1, 2))), (2, 3, (2, 2), (1, 2, 2, 3, 4), (), (1, 1), True, True))
assert_raises(TypeError, hash, (1, []))

# dict
d = {"a": 1, "b": 2}
assert_eq((d.get("a"), d.get("z"), d.get("z", 0), d.setdefault("c", 3), d.setdefault("a", 9), d.pop("c"), d.pop("z", None)), (1, None, 0, 3, 1, 3, None))
assert_eq((list(d.keys()), list(d.values()), list(d.items()), list(reversed(d)), d.popitem(), d), (["a", "b"], [1, 2], [("a", 1), ("b", 2)], ["b", "a"], ("b", 2), {"a": 1}))
d.update({"x": 1}, y=2); d.update([("z", 3)])
assert_eq(d, {"a": 1, "x": 1, "y": 2, "z": 3})
assert_eq((dict.fromkeys("ab"), dict.fromkeys([1], 0), {"a": 1} | {"b": 2}, {**{"a": 1}, "a": 2}), ({"a": None, "b": None}, {1: 0}, {"a": 1, "b": 2}, {"a": 2}))
merged = {"a": 1}
merged |= [("b", 2)]
assert_eq(merged, {"a": 1, "b": 2})
assert_raises(KeyError, {}.popitem)
assert_raises(KeyError, d.__getitem__, "missing")
keys = d.keys()
d["new"] = 0
assert_eq((len(keys), "new" in keys, keys & {"a", "q"}, keys - {"a"} == {"x", "y", "z", "new"}), (5, True, {"a"}, True))
assert_true(d.items() >= {("a", 1)})
assert_eq(d.keys().mapping["a"], 1)
def change_during_iteration():
    for k in d:
        d["other"] = 1
assert_raises(RuntimeError, change_during_iteration)
# Equal keys keep the first key object; insertion order is preserved on update.
first = {1: "int"}
first[1.0] = "float"
first[True] = "bool"
assert_eq((list(first), first[1]), ([1], "bool"))
class Missing(dict):
    def __missing__(self, key): return key * 2
assert_eq((Missing()["ab"], Missing().get("ab")), ("abab", None))

# set and frozenset
a, b2 = {1, 2, 3}, {2, 3, 4}
assert_eq((a | b2, a & b2, a - b2, a ^ b2, a <= {1, 2, 3, 4}, a < a, a.isdisjoint({5}), {1}.issubset([1, 2]), a.issuperset((1,))),
          ({1, 2, 3, 4}, {2, 3}, {1}, {1, 4}, True, False, True, True, True))
assert_eq((a.union([5], (6,)), a.intersection("x"), a.difference([1], [2]), a.symmetric_difference([3, 9])), ({1, 2, 3, 5, 6}, set(), {3}, {1, 2, 9}))
c = set()
c.add(1); c.update([2, 3], {4}); c.discard(9); c.remove(4)
c |= {5}; c &= {1, 2, 5}; c -= {1}; c ^= {7}
assert_eq(c, {2, 5, 7})
assert_raises(KeyError, c.remove, 9)
assert_raises(TypeError, lambda: {1} | [2])
f = frozenset([1, 2])
assert_eq((f | {3}, type(f | {3}), type({3} | f), hash(f) == hash(frozenset([2, 1])), {f: 1}[frozenset({1, 2})]), (frozenset({1, 2, 3}), frozenset, set, True, 1))
assert_true({1, 2} == frozenset({1, 2}))
assert_true(frozenset([1]) in {frozenset([1])})
assert_true({1} in [{1}])
assert_true(set([frozenset()]).__contains__(set()))  # a set argument is looked up as a frozenset

# range
r = range(1, 10, 3)
assert_eq((list(r), len(r), r[1], r[-1], r[::-1], r.index(7), r.count(4), 4 in r, 5 in r, r.start, r.stop, r.step), ([1, 4, 7], 3, 4, 7, range(7, -2, -3), 2, 1, True, False, 1, 10, 3))
assert_eq((range(0) == range(2, 2), range(0, 3, 2) == range(0, 4, 2), hash(range(0)) == hash(range(1, 1))), (True, True, True))
assert_raises(IndexError, r.__getitem__, 3)
assert_eq(len(range(-10**20, 10**20)) if False else range(10**20)[-1], 10**20 - 1)
assert_raises(OverflowError, len, range(10**20))

# Comparisons between different numeric types are exact.
assert_eq((2**53 + 1 == float(2**53 + 1), 2**53 + 1 > float(2**53), 1 == 1.0 == 1 + 0j, 10**400 > float("1e308"), 0.1 == 1/10), (False, True, True, True, True))
assert_eq(hash(2**61 - 1), 0)
assert_eq((hash(-1), hash(-2), hash(1.5) == hash(1.5), hash(10**20) == hash(float(10**20))), (-2, -2, True, True))

# from_bytes, bytes(), and bytearray() take only bytes-like objects and iterables; bytearray ignores __bytes__.
class WithBytes:
    def __bytes__(self): return b"\x01\x02"
    def __iter__(self): return iter([3])
assert_eq((int.from_bytes(WithBytes()), bytes(WithBytes()), bytearray(WithBytes())), (258, b"\x01\x02", bytearray(b"\x03")))
for convert, target in ((int.from_bytes, "bytes"), (bytes, "bytes"), (bytearray, "bytearray")):
    try:
        convert(1.5)
    except TypeError as error:
        assert_eq(str(error), "cannot convert 'float' object to %s" % target)
    else:
        raise AssertionError("converted a float")
assert_raises(TypeError, int.from_bytes, 5)
assert_raises(TypeError, int.from_bytes, b"\x01", b"big")

# range attributes are read-only; index() names its search; a huge range has no len().
r = range(0, 20, 2)
try:
    r.start = 1
except AttributeError as error:
    assert_eq(str(error), "readonly attribute")
else:
    raise AssertionError("range.start is writable")
for missing, message in ((11, "range.index(x): x not in range"), ("a", "sequence.index(x): x not in sequence")):
    try:
        r.index(missing)
    except ValueError as error:
        assert_eq(str(error), message)
    else:
        raise AssertionError("found %r" % missing)
assert_raises(OverflowError, len, range(2 ** 64))

# str methods report bad arguments as CPython does.
def type_error(call):
    try:
        call()
    except TypeError as error:
        return str(error)
    raise AssertionError("no TypeError")
assert_eq(type_error(lambda: "a".split(1)), "must be str or None, not int")
assert_eq(type_error(lambda: "a".partition(None)), "must be str, not NoneType")
assert_eq(type_error(lambda: "a".strip(1)), "strip arg must be None or str")
assert_eq(type_error(lambda: "a".startswith(["a"])), "startswith first arg must be str or a tuple of str, not list")
assert_eq(type_error(lambda: "a".endswith(("b", 1))), "tuple for endswith must only contain str, not int")
assert_eq(type_error(lambda: "a".find(1)), "find() argument 1 must be str, not int")
assert_eq(type_error(lambda: "a".find("a", "x")), "slice indices must be integers or have an __index__ method")
assert_eq(type_error(lambda: "a".removesuffix(None)), "removesuffix() argument must be str, not None")
assert_eq(type_error(lambda: "a".ljust(5, 1)), "The fill character must be a unicode character, not int")
assert_eq(type_error(lambda: "a".ljust()), "ljust expected at least 1 argument, got 0")
assert_eq(type_error(lambda: "a".join(1)), "can only join an iterable")
assert_eq(type_error(lambda: "a".upper(x=1)), "str.upper() takes no keyword arguments")
assert_eq(type_error(lambda: [].append(x=1)), "list.append() takes no keyword arguments")
assert_eq(type_error(lambda: "a".encode(1)), "encode() argument 'encoding' must be str, not int")
assert_eq(type_error(lambda: str("a", "utf-8")), "decoding str is not supported")
assert_eq(type_error(lambda: str.maketrans("a", 1)), "maketrans() argument 2 must be str, not int")
assert_eq("a\nb".splitlines("yes"), ["a\n", "b"])

# bytes %s and %b take any buffer, memoryview included.
assert_eq(b"%s|%b" % (memoryview(b"m"), bytearray(b"x")), b"m|x")

# bytes have no titlecase; fill bytes may be bytes or bytearray; hex and fromhex errors.
assert_true(b"AB".isupper() and bytearray(b"AB").isupper() and not b"Ab".isupper())
assert_eq(bytearray(b"a").center(4, b"*"), bytearray(b"*a**"))
assert_eq(b"a".ljust(3, bytearray(b"-")), b"a--")
for call, message in ((lambda: b"ab".hex("--"), "sep must be length 1."),
                      (lambda: bytes.fromhex("0ab"), "fromhex() arg must contain an even number of hexadecimal digits")):
    try:
        call()
    except ValueError as error:
        assert_eq(str(error), message)
    else:
        raise AssertionError(message)

# Intersecting with an iterable hashes its items as they are; adding names the set role.
assert_eq(type_error(lambda: {1}.intersection([[]])), "unhashable type: 'list'")
assert_eq(type_error(lambda: {1}.issubset([[]])), "unhashable type: 'list'")
assert_eq(type_error(lambda: {1: []}.items() & {(1, 2)}), "unhashable type: 'list'")
assert_eq(type_error(lambda: {1}.union([[]])), "cannot use 'list' as a set element (unhashable type: 'list')")
assert_eq({1, 2, 3}.intersection([3, 2, 9]), {2, 3})

# int() and float() parse bytearray and other buffers; float() takes any length.
assert_eq(int(bytearray(b"12")), 12)
assert_eq(int(bytearray(b"12"), 8), 10)
assert_eq(int(memoryview(b"123")[1:]), 23)
assert_eq(float(bytearray(b"1.5")), 1.5)
assert_eq(float(memoryview(b"2")), 2.0)
assert_eq(float("1" * 5000), float("inf"))
assert_eq(type_error(lambda: int(memoryview(b"1"), 10)), "int() can't convert non-string with explicit base")
assert_eq(type_error(lambda: int([])), "int() argument must be a string, a bytes-like object or a real number, not 'list'")
assert_eq(type_error(lambda: float(None)), "float() argument must be a string or a real number, not 'NoneType'")
try:
    int(bytearray(b"x"))
except ValueError as error:
    assert_eq(str(error), "invalid literal for int() with base 10: b'x'")
else:
    raise AssertionError("int(bytearray(b'x'))")

# The singletons' types take no arguments.
assert_eq(type_error(lambda: type(None)(1)), "NoneType takes no arguments")
assert_eq(type_error(lambda: type(...)(x=1)), "EllipsisType takes no arguments")
assert_eq(type_error(lambda: type(NotImplemented)(1)), "NotImplementedType takes no arguments")

# complex() parses a string only as its sole positional argument.
assert_eq(type_error(lambda: complex("1", 2)), "complex() argument 'real' must be a real number, not str")
assert_eq(type_error(lambda: complex(real="1")), "complex() argument 'real' must be a real number, not str")
assert_eq(type_error(lambda: complex(1, None)), "complex() argument 'imag' must be a real number, not NoneType")
assert_eq(type_error(lambda: complex([])), "complex() argument must be a string or a number, not list")

# type() names the bad argument; dir() lists __dir__'s result as list() would.
assert_eq(type_error(lambda: type("T", 1, {})), "type.__new__() argument 2 must be tuple, not int")
assert_eq(type_error(lambda: type("T", (), [])), "type.__new__() argument 3 must be dict or frozendict, not list")
assert_eq(type_error(lambda: type(1, (), {})), "type.__new__() argument 1 must be str, not int")
class BadDir:
    def __dir__(self):
        return 1
assert_eq(type_error(lambda: dir(BadDir())), "'int' object is not iterable")

# chr() takes any __index__ value; one too big for a C long is out of range.
assert_eq(type_error(lambda: chr(65.0)), "'float' object cannot be interpreted as an integer")
try:
    chr(2 ** 64)
except ValueError as error:
    assert_eq(str(error), "chr() arg not in range(0x110000)")
else:
    raise AssertionError("chr(2 ** 64)")

# exec() and eval() word their namespace errors as CPython does.
assert_eq(type_error(lambda: exec("1", [])), "exec() globals must be a dict or a frozendict, not list")
assert_eq(type_error(lambda: exec("1", {}, 1)), "locals must be a mapping or None, not int")
assert_eq(type_error(lambda: eval("1", [])), "globals must be a real dict or a frozendict; try eval(expr, {}, mapping)")
assert_eq(type_error(lambda: eval("1", 1)), "globals must be a dict or a frozendict")

# OSError's str() counts a field that was set, even to None.
error = OSError(None, "m")
assert_eq(str(error), "[Errno None] m")
error = OSError(1, "m", "f")
error.filename = None
assert_eq(str(error), "[Errno 1] m: None")
error = OSError("x")
error.filename = "f"
assert_eq(str(error), "[Errno None] None: 'f'")
assert_eq(str(OSError("x")), "x")

# A builtin class method is a classmethod_descriptor bound to its class.
fromkeys = dict.__dict__["fromkeys"]
assert_eq(type(fromkeys).__name__, "classmethod_descriptor")
assert_eq(repr(fromkeys), "<method 'fromkeys' of 'dict' objects>")
assert_eq(fromkeys(dict, "ab"), {"a": None, "b": None})
assert_eq(fromkeys.__get__({})("x"), {"x": None})
assert_eq((fromkeys.__objclass__ is dict, callable(fromkeys)), (True, True))
assert_eq(type_error(lambda: fromkeys()), "descriptor 'fromkeys' of 'dict' object needs an argument")
assert_eq(type_error(lambda: fromkeys(int, "a")), "descriptor 'fromkeys' requires a subtype of 'dict' but received 'int'")
assert_eq(type(int.__dict__["real"]).__name__, "getset_descriptor")
class Slotted:
    __slots__ = ("a",)
assert_eq(type(Slotted.a).__name__, "member_descriptor")
# sentinel's __repr__ is a slot wrapper; its other methods are descriptors.
marker = sentinel("MARKER")
assert_eq(type(marker).__repr__(marker), "MARKER")
assert_eq(str(assert_raises(TypeError, type(marker).__repr__, 1)),
          "descriptor '__repr__' requires a 'sentinel' object but received a 'int'")
assert_eq(str(assert_raises(TypeError, marker.__copy__, 1)), "sentinel.__copy__() takes no arguments (1 given)")
# A builtin function's __module__ is a writable member; the builtin types'
# own __module__ is not an attribute of their instances.
assert_eq(len.__module__, "builtins")
method = [].append
assert_eq(method.__module__, None)
method.__module__ = "m"
assert_eq((method.__module__, [].append.__module__), ("m", None))
del method.__module__
assert_eq(method.__module__, None)
error = ValueError()
assert_eq(hasattr(error, "__module__"), False)
error.__module__ = "x"
assert_eq(error.__module__, "x")
for value in (1, "s", [], 1.0, object(), slice(1), (1).__add__, str.join):
    assert_eq(hasattr(value, "__module__"), False)
    with assert_raises(AttributeError) as caught:
        value.__module__ = "x"
    assert_eq(str(caught.exception),
              "'%s' object has no attribute '__module__' and no __dict__ for setting new attributes" % type(value).__name__)
class Local: pass
assert_eq((Local().__module__, int.__module__), (__name__, "builtins"))
for name in ("__name__", "__qualname__", "__module__"):
    assert_eq(hasattr(super(Local, Local()), name), False)
# type's namespace holds data descriptors for the class attributes.
descriptors = type.__dict__
for name in ("__name__", "__qualname__", "__module__", "__bases__", "__mro__", "__dict__", "__doc__", "__type_params__"):
    assert_eq(type(descriptors[name]).__name__, "getset_descriptor")
assert_eq(type(descriptors["__base__"]).__name__, "member_descriptor")
assert_eq(descriptors["__mro__"].__get__(int), int.__mro__)
class Renamed: pass
descriptors["__name__"].__set__(Renamed, "Other")
assert_eq(Renamed.__name__, "Other")
with assert_raises(TypeError) as caught:
    descriptors["__name__"].__set__(int, "x")
assert_eq(str(caught.exception), "cannot set '__name__' attribute of immutable type 'int'")
with assert_raises(AttributeError) as caught:
    descriptors["__mro__"].__set__(Renamed, ())
assert_eq(str(caught.exception), "attribute '__mro__' of 'type' objects is not writable")
# Every type has a __doc__.
for cls in (int, object, type, ValueError):
    assert_eq("__doc__" in cls.__dict__, True)
