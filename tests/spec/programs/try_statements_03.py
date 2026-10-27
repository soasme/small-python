# spec: PLS-315 15.4
# description: Programs on try statements, each with the output CPython 3.15 gives.
from harness import *

check_program('''def clean(s):
    out = ""; i = 0
    while i < len(s):
        if s.startswith("0x", i):
            i += 2
            while i < len(s) and s[i] in "0123456789abcdef": i += 1
            out += "ADDR"
        else:
            out += s[i]; i += 1
    return out
for x in [list.append, [].append, int.__add__, (1).__add__, dict.fromkeys, object.__init__, object.__new__, int.__new__, list.__getitem__, [].__getitem__,
          dict.__contains__, {}.__contains__, set.__contains__, list.__contains__, int.__round__, (1).__round__, object.__format__, str.upper, "a".upper,
          list.__reversed__, float.__floor__, object.__repr__, object().__repr__, print, len, int.__init_subclass__, list.__class_getitem__]:
    print(type(x).__name__, clean(repr(x)))
print(type(list.append) is type(str.upper), type(list.append).__module__, type(int.__add__))
try: type(list.append)()
except TypeError as e: print(e)
''',
              '''method_descriptor <method 'append' of 'list' objects>
builtin_function_or_method <built-in method append of list object at ADDR>
wrapper_descriptor <slot wrapper '__add__' of 'int' objects>
method-wrapper <method-wrapper '__add__' of int object at ADDR>
builtin_function_or_method <built-in method fromkeys of type object at ADDR>
wrapper_descriptor <slot wrapper '__init__'>
builtin_function_or_method <built-in method __new__ of type object at ADDR>
builtin_function_or_method <built-in method __new__ of type object at ADDR>
method_descriptor <method '__getitem__' of 'list' objects>
builtin_function_or_method <built-in method __getitem__ of list object at ADDR>
method_descriptor <method '__contains__' of 'dict' objects>
builtin_function_or_method <built-in method __contains__ of dict object at ADDR>
method_descriptor <method '__contains__' of 'set' objects>
wrapper_descriptor <slot wrapper '__contains__' of 'list' objects>
method_descriptor <method '__round__' of 'int' objects>
builtin_function_or_method <built-in method __round__ of int object at ADDR>
method_descriptor <method '__format__'>
method_descriptor <method 'upper' of 'str' objects>
builtin_function_or_method <built-in method upper of str object at ADDR>
method_descriptor <method '__reversed__' of 'list' objects>
method_descriptor <method '__floor__' of 'float' objects>
wrapper_descriptor <slot wrapper '__repr__'>
method-wrapper <method-wrapper '__repr__' of object object at ADDR>
function <function run_program.<locals>.print_ at ADDR>
builtin_function_or_method <built-in function len>
builtin_function_or_method <built-in method __init_subclass__ of type object at ADDR>
builtin_function_or_method <built-in method __class_getitem__ of type object at ADDR>
True builtins <class 'wrapper_descriptor'>
cannot create 'method_descriptor' instances
''')

check_program('''print(object.__subclasshook__(int), int.__subclasshook__(1), type(object.__subclasshook__).__name__)
class A:
    @classmethod
    def __subclasshook__(cls, C): return True
print(A.__subclasshook__(int), issubclass(int, A))
for args in [(), (1, 2)]:
    try: object.__subclasshook__(*args)
    except TypeError as e: print(e)
try: object.__subclasshook__(x=1)
except TypeError as e: print(e)
''',
              '''NotImplemented NotImplemented builtin_function_or_method
True False
object.__subclasshook__() takes exactly one argument (0 given)
object.__subclasshook__() takes exactly one argument (2 given)
object.__subclasshook__() takes no keyword arguments
''')

check_program('''for x in [iter([]), iter(()), iter(""), iter("é"), iter({}), iter(set()), iter(frozenset()), iter(range(1)), iter(range(2**70)), iter(b""), iter(bytearray()),
          map(abs, []), zip(), enumerate([]), reversed([]), reversed((1,)), reversed("ab"), filter(None, []), iter({}.items()), iter({}.values()), iter({}.keys()),
          reversed({}), reversed({}.values()), reversed({}.items()), iter(lambda: 1, 2), reversed(range(3)), iter(t"a{1}")]:
    print(type(x).__name__, type(x) is type(x), type(x).__module__)
print(type(map) is type, isinstance(map(abs, []), map), isinstance(zip(), zip), isinstance(enumerate([]), enumerate), isinstance(reversed([]), reversed), isinstance(filter(None, []), filter))
print(map, zip, list(map(abs, [-1, 2])), list(zip("ab", [1, 2], strict=True)), list(enumerate("ab", start=1)), list(filter(None, [0, 1])), list(reversed("ab")))
it = iter([1, 2, 3])
print(it.__next__(), next(it), it.__iter__() is it, type(it).__next__(it))
try: it.__next__()
except StopIteration: print("stop")
m = map(str, [1]); print(m.__next__(), iter(m) is m, map.__next__)
try: type(iter([])).__next__(iter(()))
except TypeError as e: print(e)
try: type(iter([]))()
except TypeError as e: print(e)
try: map()
except TypeError as e: print(e)
try: iter(1, 2)
except TypeError as e: print(e)
n = [0]
def counter():
    n[0] += 1
    return n[0]
print(list(iter(counter, 4)))
def raiser():
    raise StopIteration
print(list(iter(raiser, 0)))
ci = iter(counter, 8); print(next(ci), next(ci), list(ci), list(ci))
lines = iter(["a", "b", "", "c"]).__next__
print(list(iter(lines, "")))
for kw in [dict(start=2), dict(iterable='ab'), dict(iterable='ab', start=3), dict(start=3, iterable='ab'), dict(x=1)]:
    try: print(list(enumerate(**kw)))
    except TypeError as e: print(e)
for call in [lambda: enumerate('a', 1, start=2), lambda: enumerate('a', start='x'), lambda: enumerate(), lambda: zip(x=1)]:
    try: print(list(call()))
    except TypeError as e: print(e)
for a in [([1], [1, 2]), ([1, 2], [1]), ([1], [1], [1, 2]), ([1, 2], [1, 2], [1]), ([], []), ((), "", [])]:
    try: print(list(zip(*a, strict=True)))
    except ValueError as e: print(e)
print(list(zip([1], [1, 2], strict=False)), list(enumerate("ab", 5)))
for f, a in [(reversed, ()), (reversed, (1, 2)), (map, (abs,)), (enumerate, (1, 2, 3)), (filter, ()), (filter, (1, 2, 3)), (iter, ()), (iter, (1, 2, 3))]:
    try: f(*a)
    except TypeError as e: print(e)
''',
              '''list_iterator True builtins
tuple_iterator True builtins
str_ascii_iterator True builtins
str_iterator True builtins
dict_keyiterator True builtins
set_iterator True builtins
set_iterator True builtins
range_iterator True builtins
longrange_iterator True builtins
bytes_iterator True builtins
bytearray_iterator True builtins
map True builtins
zip True builtins
enumerate True builtins
list_reverseiterator True builtins
reversed True builtins
reversed True builtins
filter True builtins
dict_itemiterator True builtins
dict_valueiterator True builtins
dict_keyiterator True builtins
dict_reversekeyiterator True builtins
dict_reversevalueiterator True builtins
dict_reverseitemiterator True builtins
callable_iterator True builtins
range_iterator True builtins
TemplateIter True string.templatelib
True True True True False True
<class 'map'> <class 'zip'> [1, 2] [('a', 1), ('b', 2)] [(1, 'a'), (2, 'b')] [1] ['b', 'a']
1 2 True 3
stop
1 True <slot wrapper '__next__' of 'map' objects>
descriptor '__next__' requires a 'list_iterator' object but received a 'tuple_iterator'
cannot create 'list_iterator' instances
map() must have at least two arguments.
iter(v, w): v must be callable
[1, 2, 3]
[]
5 6 [7] []
['a', 'b']
'start' is an invalid keyword argument for enumerate()
[(0, 'a'), (1, 'b')]
[(3, 'a'), (4, 'b')]
[(3, 'a'), (4, 'b')]
'x' is an invalid keyword argument for enumerate()
enumerate() takes at most 2 arguments (3 given)
'str' object cannot be interpreted as an integer
enumerate() missing required argument 'iterable'
zip() got an unexpected keyword argument 'x'
zip() argument 2 is longer than argument 1
zip() argument 2 is shorter than argument 1
zip() argument 3 is longer than arguments 1-2
zip() argument 3 is shorter than arguments 1-2
[]
[]
[(1, 1)] [(5, 'a'), (6, 'b')]
reversed expected 1 argument, got 0
reversed expected 1 argument, got 2
map() must have at least two arguments.
enumerate() takes at most 2 arguments (3 given)
filter expected 2 arguments, got 0
filter expected 2 arguments, got 3
iter expected at least 1 argument, got 0
iter expected at most 2 arguments, got 3
''')

check_program('class I:\n    def __index__(self): return 5\n    def __repr__(self): return \'I()\'\nclass F:\n    def __float__(self): return 2.5\nclass N:\n    def __int__(self): return 7\nclass B:\n    def __bytes__(self): return b"BB"\nclass Bad:\n    def __bytes__(self): return "x"\nclass M:\n    def __getitem__(self, k): return k * 2\n    def __repr__(self): return \'M()\'\ntests = [("%5.2f|%-4d|%x|%o|%e|%c|%r|%a|%%", (3.14159, 7, 255, 8, 12345.678, 65, "q", "é")), ("%(a)s-%(b)03d", {"a": 1, "b": 2}),\n         ("%+d % d %#x %#o %05.1f %.3s %*d", (5, 5, 255, 8, 2.25, "abcdef", 4, 7)),\n         ("%d", "x"), ("%x", 1.5), ("%f", "x"), ("%c", "ab"), ("%c", 0x110000), ("%c", 1.5), ("%*d", ("x", 1)), ("%(a)s", 1), ("%(a", {"a": 1}), ("%y", 1), ("%", 1), ("%s %s", (1,)), ("%s", (1, 2)), ("%(a)s", {}), ("%.*f", (2, 1.2345)), ("%s", {"a": 1}), ("%(a)s %s", {"a": 1}),\n         ("%.3d|%-6.3x|%06.2f|%-06d|%+.2e|% d|%#.3o", (5, 255, 3.14159, 7, 1234.5, 3, 8)),\n         ("%s", ()), ("%d", True), ("%i", 3.99), ("%x", True), ("%5c|%-3c|", ("x", 65)), ("%.1s %r %a", ("hello", "é", "é")), ("%#g %g %G %E", (1.0, 1e20, 1e-20, 2.0)), ("%010.3f|%-10.1f|%+010d", (-3.14159, 2.5, 42)), ("%%%s", "x"), ("%d", 10**30), ("%x", -(10**20)), ("%(x)s %(x)s", {"x": 1}),\n         ("%ld %5.1lf", (1, 2.25)), ("%s", None), ("%r", [1, "a"]), ("%.0f %.0e", (0.5, 1.5)), ("%-+5d|", 3), ("%*.*f|", (8, 2, 3.14159)), ("%-*d|", (4, 1)), ("%*d|", (-4, 1)),\n         ("%s %d", (1, "x")), ("%(a)d", {"a": "x"}), ("%s %s", 1), ("", 1), ("x", (1,)), ("", ()), ("", {}), ("%s", [1]), ("%(a)s", [1]), ("%s %*d", (1, 2.5, 3)), ("%.*d", ("q", 1)), ("%c", -1), ("%(a)c", {"a": "xy"}), ("%z", 1), ("%5", 1), ("abc %", ()), ("%(a)*d", {"a": 1}), ("%s", "x"), ("%d %s", ([], 1)), ("%c", 1.0),\n         ("%d", I()), ("%x", I()), ("%f", I()), ("%f", F()), ("%d", F()), ("%d", N()), ("%x", N()), ("%c", I()), ("%s", M()), ("%(ab)s", M()),\n         ("%s %(a)s", {"a": 1}), ("%(a)s %%", {"a": 1}), ("%-(a)5s|", {"a": 1}), ("%(a)-5s|", {"a": 1}), ("%(a)s", (1,)), ("%(a)s", "x"), ("%(a)s %(b)s", {"a": 1}), ("%s", b"x"), ("%5.1z", 1), ("%(a)", {"a": 1}), ("%(a)5", {"a": 1}), ("é%y", 1), ("%c", "é"), ("%10.4r|", "abcdef"), ("%x", 3.0), ("%.2147483648f", 1.0), ("%c", True), ("%#x %#X %#o", (0, 0, 0)), ("%e", 10**400),\n         ("%!", 1), ("%\'", 1), ("%é", 1), ("%\\x01", 1), ("%5.2s|%-5.2s|%05s|", ("abc", "abc", "ab")), ("%#5x|%#-6X|%#06o|% #x", (255, 255, 8, 15)), ("%+.3d|% 05d|%-+08.3f", (-5, -3, 2.5)), ("%f %F %e", (float("inf"), float("nan"), float("-inf"))), ("%s%s", ("é", "ü")), ("%-4s|%4s|", ("é", "ü")), ("%r", "x" * 3), ("%((a))s", {"(a)": 1}), ("%s", I())]\nfor fmt, args in tests:\n    try: print(repr(fmt % args))\n    except Exception as e: print(type(e).__name__, e)\nbtests = [(b"%d-%s", (1, b"x")), (b"%s", "x"), (b"%c%c", (65, b"b")), (b"%r %a", ("é", "é")), (b"%5.1f|%x", (2.25, 255)), (b"%s", bytearray(b"z")), (b"%b", b"q"), (b"%c", 256), (b"%c", b"ab"), (b"%c", bytearray(b"ab")), (b"%c", "a"),\n          (b"%s", B()), (b"%s", Bad()), (b"%(a)s", {b"a": b"v"}), (b"%(a)s", {"a": 1}), (b"%s", (1, 2)), (b"%s", [b"x"]), (b"%y", 1), (b"%\\x01", 1), (b"%5s|%-5b|", (b"ab", b"cd")), (b"%.1s|%.2a", (b"xyz", "abc")), (b"%5c|", 65), (b"%(a)s", b"x"), (b"%d %d", 1)]\nprint(repr(bytearray(b"%d!") % 5), type(bytearray(b"%s") % b"x").__name__)\nclass S(str):\n    def __rmod__(self, other): return "rmod"\n',
              '" 3.14|7   |ff|10|1.234568e+04|A|\'q\'|\'\\\\xe9\'|%"\n\'1-002\'\n\'+5  5 0xff 0o10 002.2 abc    7\'\nTypeError format argument: %d requires a real number, not str\nTypeError format argument: %x requires an integer, not float\nTypeError format argument: %f requires a real number, not str\nTypeError format argument: %c requires an integer or a unicode character, not a string of length 2\nOverflowError format argument: %c argument not in range(0x110000)\nTypeError format argument: %c requires an integer or a unicode character, not float\nTypeError format argument 1: * requires int, not str\nTypeError format requires a mapping, not int\nValueError stray % or incomplete format key at position 0\nValueError unsupported format %y at position 0\nValueError stray % at position 0\nTypeError not enough arguments for format string (got 1)\nTypeError not all arguments converted during string formatting (required 1, got 2)\nKeyError \'a\'\n\'1.23\'\n"{\'a\': 1}"\nValueError format requires a parenthesised mapping key at position 6\n\'005|0ff   |003.14|7     |+1.23e+03| 3|0o010\'\nTypeError not enough arguments for format string (got 0)\n\'1\'\n\'3\'\n\'1\'\n\'    x|A  |\'\n"h \'é\' \'\\\\xe9\'"\n\'1.00000 1e+20 1E-20 2.000000E+00\'\n\'-00003.142|2.5       |+000000042\'\n\'%x\'\n\'1000000000000000000000000000000\'\n\'-56bc75e2d63100000\'\n\'1 1\'\n\'1   2.2\'\n\'None\'\n"[1, \'a\']"\n\'0 2e+00\'\n\'+3   |\'\n\'    3.14|\'\n\'1   |\'\n\'1   |\'\nTypeError format argument 2: %d requires a real number, not str\nTypeError format argument \'a\': %d requires a real number, not str\nTypeError not enough arguments for format string (got 1)\nTypeError not all arguments converted during string formatting (required 0, got 1)\nTypeError not all arguments converted during string formatting (required 0, got 1)\n\'\'\n\'\'\n\'[1]\'\nTypeError list indices must be integers or slices, not str\nTypeError format argument 2: * requires int, not float\nTypeError format argument 1: * requires int, not str\nOverflowError format argument: %c argument not in range(0x110000)\nTypeError format argument \'a\': %c requires an integer or a unicode character, not a string of length 2\nValueError unsupported format %z at position 0\nValueError stray % at position 0\nValueError stray % at position 4\nValueError * cannot be used with a parenthesised mapping key at position 0\n\'x\'\nTypeError format argument 1: %d requires a real number, not list\nTypeError format argument: %c requires an integer or a unicode character, not float\n\'5\'\n\'5\'\n\'5.000000\'\n\'2.500000\'\nTypeError format argument: %d requires a real number, not F\n\'7\'\nTypeError format argument: %x requires an integer, not N\n\'\\x05\'\n\'M()\'\n\'abab\'\n"{\'a\': 1} 1"\n\'1 %\'\nValueError stray % at position 0 or unexpected format character \'(\' at position 2\n\'1    |\'\nTypeError format requires a mapping, not tuple\nTypeError format requires a mapping, not str\nKeyError \'b\'\n"b\'x\'"\nValueError unsupported format %z at position 0\nValueError stray % at position 0\nValueError stray % at position 0\nValueError unsupported format %y at position 1\n\'é\'\n"      \'abc|"\nTypeError format argument: %x requires an integer, not float\nValueError precision too big at position 0\n\'\\x01\'\n\'0x0 0X0 0o0\'\nOverflowError int too large to convert to float\nValueError stray % at position 0 or unexpected format character \'!\' at position 1\nValueError stray % at position 0 or unexpected format character "\'" at position 1\nValueError stray % at position 0 or unexpected format character \'é\' (U+00E9) at position 1\nValueError stray % at position 0 or unexpected format character U+0001 at position 1\n\'   ab|ab   |   ab|\'\n\' 0xff|0XFF  |0o0010| 0xf\'\n\'-005|-0003|+2.500  \'\n\'inf NAN -inf\'\n\'éü\'\n\'é   |   ü|\'\n"\'xxx\'"\n\'1\'\n\'I()\'\nbytearray(b\'5!\') bytearray\n')

check_program('''for v in [[1], (1,), 'a', b'a', bytearray(b'a'), range(1)]:
    for k in [5, "x", 1.5]:
        try: v[k]
        except (IndexError, TypeError) as e: print(type(e).__name__, e)
for v in [[1], bytearray(b'a')]:
    for k in [5, "x"]:
        try: v[k] = 1
        except (IndexError, TypeError) as e: print(type(e).__name__, e)
        try: del v[k]
        except (IndexError, TypeError) as e: print(type(e).__name__, e)
''',
              '''IndexError list index out of range
TypeError list indices must be integers or slices, not str
TypeError list indices must be integers or slices, not float
IndexError tuple index out of range
TypeError tuple indices must be integers or slices, not str
TypeError tuple indices must be integers or slices, not float
IndexError string index out of range
TypeError string indices must be integers, not 'str'
TypeError string indices must be integers, not 'float'
IndexError index out of range
TypeError byte indices must be integers or slices, not str
TypeError byte indices must be integers or slices, not float
IndexError bytearray index out of range
TypeError bytearray indices must be integers or slices, not str
TypeError bytearray indices must be integers or slices, not float
IndexError range object index out of range
TypeError range indices must be integers or slices, not str
TypeError range indices must be integers or slices, not float
IndexError list assignment index out of range
IndexError list assignment index out of range
TypeError list indices must be integers or slices, not str
TypeError list indices must be integers or slices, not str
IndexError bytearray index out of range
IndexError bytearray index out of range
TypeError bytearray indices must be integers or slices, not str
TypeError bytearray indices must be integers or slices, not str
''')

check_program('nan = float(\'nan\'); inf = float(\'inf\')\nclass MyInt(int): pass\nfor v, s in [(-nan, \'+.2e\'), (inf, \'+F\'), (-0.0, \'\'), (1e16, \'.20\'), (123.0, \'.2\'), (100.0, \'#.3\'),\n             (1.5, \'#.0f\'), (1.5, \'#g\'), (-0.0001, \'z.2f\'), (-0.0, \'z.3g\'), (1, \'٣\'), (12345678, \'_\'),\n             (0xdeadbeef, \'_x\'), (1234.56789, \',.2f\'), (1234.56789, \',._f\'), (-12345, \'010,\'), (12345, \'=+12,\'),\n             (1234, \'^11,\'), (1 + 2j, \'.2f\'), (-0.0 + 1j, \'\'), (complex(-0.0, -0.0), \'\'), (1 + 1j, \'^15.3e\'),\n             (65, \'c\'), (97, \'05c\'), (255, \'#X\'), (255, \'#012_b\'), (3.5, \'%\'), (1e100, \'n\'), (12345, \'n\'),\n             (-2**70, \'_x\'), (True, \'x\'), (MyInt(7), \'03\'), (\'héllo\', \'*^9.3\'), (3, \'€^9\'), (1234567.891, \'020_.3_f\')]:\n    print(repr(format(v, s)))\nfor v, s in [(\'abc\', \'+\'), (\'abc\', \' \'), (\'abc\', \'z\'), (\'abc\', \'#\'), (\'abc\', \'=\'), (\'abc\', \'d\'), (5, \'.2\'), (5, \'z\'),\n             (97, \'+c\'), (97, \'#c\'), (0x110000, \'c\'), (5, \',_\'), (5, \'_,\'), (5, \',x\'), (5, \'.\'), (5, \'xx\'),\n             (1.0, \'d\'), (1j, \'%\'), (1j, \'010\'), (1j, \'=10\'), (None, \'x\'), (5, \'n_\'), (1.0, \'.,_f\'), (5, \'9\' * 30),\n             (5, \'\\x01\'), (1.0, \'.2n,\'), (MyInt(1), \'q\')]:\n    try: format(v, s)\n    except (ValueError, TypeError, OverflowError) as e: print(type(e).__name__, e)\nprint(f"{1234567:,} {3.14159:_.2f} {\'x\':*>4} {97:c}")\n',
              "'+nan'\n'+INF'\n'-0.0'\n'10000000000000000.0'\n'1.2e+02'\n'1.00e+02'\n'2.'\n'1.50000'\n'0.00'\n'0'\n'  1'\n'12_345_678'\n'dead_beef'\n'1,234.57'\n'1,234.567_890'\n'-0,012,345'\n'+     12,345'\n'   1,234   '\n'1.00+2.00j'\n'1j'\n'(-0-0j)'\n'1.000e+00+1.000e+00j'\n'A'\n'0000a'\n'0XFF'\n'0b0_1111_1111'\n'350.000000%'\n'1e+100'\n'12345'\n'-40_0000_0000_0000_0000'\n'1'\n'007'\n'***hél***'\n'€€€€3€€€€'\n'0_000_001_234_567.891'\nValueError Sign not allowed in string format specifier\nValueError Space not allowed in string format specifier\nValueError Negative zero coercion (z) not allowed in string format specifier\nValueError Alternate form (#) not allowed in string format specifier\nValueError '=' alignment not allowed in string format specifier\nValueError Unknown format code 'd' for object of type 'str'\nValueError Precision not allowed in integer format specifier\nValueError Negative zero coercion (z) not allowed in integer format specifier\nValueError Sign not allowed with integer format specifier 'c'\nValueError Alternate form (#) not allowed with integer format specifier 'c'\nOverflowError %c arg not in range(0x110000)\nValueError Cannot specify both ',' and '_'.\nValueError Cannot specify both ',' and '_'.\nValueError Cannot specify ',' with 'x'.\nValueError Format specifier missing precision\nValueError Invalid format specifier 'xx' for object of type 'int'\nValueError Unknown format code 'd' for object of type 'float'\nValueError Unknown format code '%' for object of type 'complex'\nValueError Zero padding is not allowed in complex format specifier\nValueError '=' alignment flag is not allowed in complex format specifier\nTypeError unsupported format string passed to NoneType.__format__\nValueError Invalid format specifier 'n_' for object of type 'int'\nValueError Cannot specify both ',' and '_'.\nValueError Too many decimal digits in format string\nValueError Unknown format code '\\x1' for object of type 'int'\nValueError Invalid format specifier '.2n,' for object of type 'float'\nValueError Unknown format code 'q' for object of type 'MyInt'\n1,234,567 3.14 ***x a\n")

check_program('''class P:
    x = 3
    def __format__(self, spec): return 'P' + spec
class D(dict):
    def __missing__(self, key): return key.upper()
print("{0[1]} {1.real} {a[k]} {a[0]}".format([5, 6], 2 + 3j, a={'k': 'v', 0: 'z'}))
print("{0:{1}{2}}|{0.x}|{1!r:>5}".format(P(), 'a', 'b'))
print("{:{w}.{p}f}".format(3.14159, w=10, p=2), "{0[١]}".format('xy'), "{a}{b}".format_map(D(a=1)))
for t in ["{0}{}", "{}{1}", "{0[}", "{0.}", "{0]}", "{", "}", "{0!x}", "{0!}", "{0:{1:{2}}}", "{5}", "{a}",
          "{0[2]}", "{0[0]x}", "{0!r", "{0!rx}", "{0[0}", "{a{}", "{0:>{1}}"]:
    try: t.format([1], 'a', 3)
    except (ValueError, KeyError, IndexError, TypeError) as e: print(type(e).__name__, e)
try: "{0}".format_map({})
except ValueError as e: print(e)
''',
              '''6 2.0 v z
Pab|3|  'a'
      3.14 y 1B
ValueError cannot switch from manual field specification to automatic field numbering
ValueError cannot switch from automatic field numbering to manual field specification
ValueError expected '}' before end of string
ValueError Empty attribute in format string
KeyError '0]'
ValueError Single '{' encountered in format string
ValueError Single '}' encountered in format string
ValueError Unknown conversion specifier x
ValueError unmatched '{' in format spec
ValueError Max string recursion exceeded
IndexError Replacement index 5 out of range for positional args tuple
KeyError 'a'
IndexError list index out of range
ValueError Only '.' or '[' may follow ']' in format field specifier
ValueError unmatched '{' in format spec
ValueError expected ':' after conversion specifier
ValueError expected '}' before end of string
ValueError unexpected '{' in field name
TypeError unsupported format string passed to list.__format__
Format string contains positional fields
''')

check_program('''# property, classmethod and staticmethod subclasses.
x = property.__new__(property)
print(type(x), x.fget)
class P(property):
    "P doc"
class Q(property): pass
def g(self):
    "get doc"
    return 42
class C:
    a = P(g)
    b = Q(g, doc="explicit")
    @P
    def c(self): return 5
    @c.setter
    def c(self, v): print("set", v)
    cm = classmethod(lambda cls: cls.__name__)
print(C().a, C.a.__doc__, C.b.__doc__, type(C.c).__name__, C().c, vars(C.a))
C().c = 9
try: del C().c
except AttributeError as e: print(e)
class CM(classmethod):
    pass
class SM(staticmethod):
    pass
class D:
    @CM
    def f(cls, x): return (cls.__name__, x)
    @SM
    def h(x): return x * 2
print(D.f(1), D().f(2), D.h(3), D().h(4), repr(D.__dict__['f'])[:20], D.__dict__['h'].__func__.__name__)
print(vars(D.__dict__['f']).keys(), D.__dict__['h'](5), isinstance(D.__dict__['f'], classmethod))
''',
              '''<class 'property'> None
42 get doc explicit P 5 {'__doc__': 'get doc'}
set 9
property 'c' of 'C' object has no deleter
('D', 1) ('D', 2) 6 8 <classmethod(<functi h
dict_keys(['__module__', '__name__', '__qualname__', '__doc__']) 10 True
''')

check_program('''# property accessor errors name the property and owner.
class C:
    x = property(lambda s: 1)
    y = property()
    z = property(None, lambda s, v: None)
for f in [lambda: setattr(C(), "x", 1), lambda: delattr(C(), "x"), lambda: C().y, lambda: delattr(C(), "z"),
          lambda: property.__get__(C.x, None, None), lambda: C.x.__set__(C(), 1), lambda: classmethod(), lambda: staticmethod(1, 2)]:
    try: print(f())
    except Exception as e: print(type(e).__name__, e)
print(repr(classmethod(len)), repr(staticmethod(len)))
''',
              '''AttributeError property 'x' of 'C' object has no setter
AttributeError property 'x' of 'C' object has no deleter
AttributeError property 'y' of 'C' object has no getter
AttributeError property 'z' of 'C' object has no deleter
TypeError __get__(None, None) is invalid
AttributeError property 'x' of 'C' object has no setter
TypeError classmethod expected 1 argument, got 0
TypeError staticmethod expected 1 argument, got 2
<classmethod(<built-in function len>)> <staticmethod(<built-in function len>)>
''')

check_program('''# Sequence repetition and slicing take any __index__; int subclasses index directly.
class N:
    def __init__(self, i): self.i = i
    def __index__(self): return self.i
class T(int):
    def __index__(self): return int(self)
class B:
    def __index__(self): return 'x'
def t(f):
    try: print(repr(f()))
    except Exception as e: print(type(e).__name__, e)
for seq in ([1, 2], (1, 2), 'ab', b'ab', bytearray(b'ab')):
    t(lambda: seq * N(2)); t(lambda: N(2) * seq); t(lambda: seq.__mul__(N(2))); t(lambda: seq.__rmul__(N(2)))
    t(lambda: seq * 2.0); t(lambda: seq.__mul__(2.0))
l = [1]; l *= N(3); print(l, l.__imul__(N(1)) is l)
r = list(range(10))
t(lambda: r[T(5):T(10)]); t(lambda: slice(T()).indices(0)); t(lambda: slice(B()).indices(0)); t(lambda: r[B()])
t(lambda: int(T(5))); t(lambda: 'abc' * 10**30)
''',
              '''[1, 2, 1, 2]
[1, 2, 1, 2]
[1, 2, 1, 2]
[1, 2, 1, 2]
TypeError can't multiply sequence by non-int of type 'float'
TypeError 'float' object cannot be interpreted as an integer
(1, 2, 1, 2)
(1, 2, 1, 2)
(1, 2, 1, 2)
(1, 2, 1, 2)
TypeError can't multiply sequence by non-int of type 'float'
TypeError 'float' object cannot be interpreted as an integer
'abab'
'abab'
'abab'
'abab'
TypeError can't multiply sequence by non-int of type 'float'
TypeError 'float' object cannot be interpreted as an integer
b'abab'
b'abab'
b'abab'
b'abab'
TypeError can't multiply sequence by non-int of type 'float'
TypeError 'float' object cannot be interpreted as an integer
bytearray(b'abab')
bytearray(b'abab')
bytearray(b'abab')
bytearray(b'abab')
TypeError can't multiply sequence by non-int of type 'float'
TypeError 'float' object cannot be interpreted as an integer
[1, 1, 1] True
[5, 6, 7, 8, 9]
(0, 0, 1)
TypeError B.__index__() must return an int, not str
TypeError B.__index__() must return an int, not str
5
OverflowError cannot fit 'int' into an index-sized integer
''')

check_program('# Named Unicode escapes: names, aliases, any case, derived and Hangul names; f-string braces.\nprint(ascii("\\N{EM DASH}\\N{LF}\\N{latin small letter a}\\N{CJK UNIFIED IDEOGRAPH-4E00}\\N{HANGUL SYLLABLE GAG}\\N{TANGUT IDEOGRAPH-17000}"))\nx = 1\nprint(ascii(f"{x}\\N{DIGIT ONE}{x!r  }"), ascii(rf"\\N{x}"), b"\\N{A}", f"{x = # note\n  }")\nfor src in [r\'"\\N{NOPE}"\', r\'"\\N{A"\', r\'"\\N"\', r\'"\\N{}"\', r\'"\\N{CJK UNIFIED IDEOGRAPH-FFFF}"\', r\'"\\N{HANGUL SYLLABLE XX}"\']:\n    try: print(ascii(eval(src)))\n    except SyntaxError as e: print(type(e).__name__)\n',
              "'\\u2014\\na\\u4e00\\uac01\\U00017000'\n'111' '\\\\N1' b'\\\\N{A}' x = \n  1\nSyntaxError\nSyntaxError\nSyntaxError\nSyntaxError\nSyntaxError\nSyntaxError\n")

check_program('# Closure cells, co_freevars/co_cellvars (with pass-through and __class__), and nested global declarations.\ndef f():\n    x = 1\n    def g():\n        def h(): return x\n        return h\n    return g\ng = f()\nprint(g.__code__.co_freevars, f.__code__.co_cellvars, g().__code__.co_freevars, g.__closure__ is g.__closure__)\ndef f2():\n    x = 1\n    class C:\n        def m(self): return x, __class__\n        def n(self): return super()\n    return C\nC = f2()\nprint(C.m.__code__.co_freevars, C.n.__code__.co_freevars, C.m.__closure__[0].cell_contents is C)\ndef f3():\n    a = b = 1\n    def g(): nonlocal b; b = 5; return a\n    return g\ng3 = f3()\nprint(g3.__closure__[1].cell_contents, g3(), g3.__closure__[1].cell_contents)\ng3.__closure__[0].cell_contents = 10; print(g3())\ndel g3.__closure__[0].cell_contents\nfor bad in [g3, lambda: g3.__closure__[0].cell_contents, lambda: setattr(g3, \'__closure__\', None), lambda: hash(g3.__closure__[1]),\n            lambda: eval(g3.__code__), lambda: exec(g3.__code__, {}), lambda: type(g3.__closure__[0])(1, 2)]:\n    try: bad()\n    except Exception as e: print(type(e).__name__, e)\nCT = type(g3.__closure__[0])\nprint((lambda: 0).__closure__, CT() < CT(1), CT(1) < CT(2), CT(1) == CT(1), CT() == CT(), repr(CT()).endswith(\': empty>\'))\nglob, loc = {}, {}\nexec("def f():\\n y = 1\\n def g():\\n  global y\\n  return y\\n def h(): return y + 1\\n return g, h\\ny = 9\\ng, h = f()\\nr = g(), h()", glob, loc)\nprint(loc[\'r\'], glob[\'y\'], \'y\' in loc)\n',
              '''('x',) ('x',) ('x',) True
('__class__', 'x') ('__class__',) True
1 1 5
10
NameError cannot access free variable 'a' where it is not associated with a value in enclosing scope
ValueError Cell is empty
AttributeError readonly attribute
TypeError unhashable type: 'cell'
TypeError code object passed to eval() may not contain free variables
TypeError code object requires a closure of exactly length 2
TypeError cell expected at most 1 argument, got 2
None True True True True True
(9, 2) 9 False
''')

check_program('''# Membership on objects that are neither containers nor iterable.
class Plain: pass
class BadIter:
    def __iter__(self): raise TypeError('mine')
class NotIt:
    def __iter__(self): return 5
for t in ['1 in Plain()', '1 not in Plain()', '1 in 5', '1 in None', '1 in BadIter()', '1 in NotIt()']:
    try: eval(t)
    except TypeError as e: print(e)
''',
              '''argument of type 'Plain' is not a container or iterable
argument of type 'Plain' is not a container or iterable
argument of type 'int' is not a container or iterable
argument of type 'NoneType' is not a container or iterable
argument of type 'BadIter' is not a container or iterable
argument of type 'NotIt' is not a container or iterable
''')

check_program('''def lh(o):
    try: return len(o)
    except TypeError: pass
    try: h = type(o).__length_hint__
    except AttributeError: return 0
    v = h(o)
    return 0 if v is NotImplemented else v
it=iter([1,2,3]); print(lh(it)); next(it); print(lh(it), type(it).__length_hint__)
print(lh(iter(range(10))), lh(reversed(range(5))), lh(iter("héllo")), lh(iter({1:2})), lh(reversed([1,2])), lh(iter({1,2})))
print(lh(iter(range(10**20, 10**20+7, 3))), lh(reversed({1:1,2:2})), lh(iter(b"ab")), lh(iter((1,))))
class B:
    def __iter__(self): return iter(range(3))
    def __len__(self): raise RuntimeError("hello")
for f in (list, [].extend, bytearray().extend, tuple):
    try: f(B())
    except RuntimeError as e: print("RT", e)
class S:
    def __getitem__(self, i):
        if i < 4: return i
        raise IndexError
    def __len__(self): return 4
class T(S):
    __len__ = None
print(lh(iter(S())), lh(reversed(S())))
it = iter(T())
try: type(it).__length_hint__(it)
except TypeError as e: print(e)
try: type(iter([])).__length_hint__(iter(()))
except TypeError as e: print(e)
d = {1:1,2:2}; it = iter(d); next(it); print(lh(it)); d[3]=3; print(lh(it))
r = iter(range(3)); list(r); print(lh(r))
print(hasattr(map(int, []), "__length_hint__"), hasattr(enumerate([]), "__length_hint__"), hasattr(iter(int, 1), "__length_hint__"))
''',
              '''3
2 <method '__length_hint__' of 'list_iterator' objects>
10 5 5 1 2 2
3 2 2 1
RT hello
RT hello
RT hello
4 4
'NoneType' object is not callable
descriptor '__length_hint__' for 'list_iterator' objects doesn't apply to a 'tuple_iterator' object
1
0
0
False False False
''')

check_program('''class MyEG(ExceptionGroup): pass
excs = [ValueError(1), TypeError(2)]
eg = MyEG('test', excs)
print(repr(eg)); excs.clear(); print(repr(eg), eg.args, eg.__dict__)
print(repr(BaseExceptionGroup('test', (ValueError(1), KeyboardInterrupt(2)))))
class Seq:
    def __init__(self, items): self.items = items
    def __len__(self): return len(self.items)
    def __getitem__(self, i): return self.items[i]
    def __repr__(self): return "Seq(%r)" % self.items
s = Seq([ValueError(1)]); eg = ExceptionGroup('t', s); s.items.append(TypeError(3)); print(repr(eg), eg.exceptions, str(eg))
for v in ({1: 2}, 5, "ab", None):
    try: ExceptionGroup("m", v)
    except (TypeError, ValueError) as e: print(type(e).__name__, e)
eg = ExceptionGroup('eg', [TypeError(1), OSError(2)])
for n in ("message", "exceptions"):
    try: setattr(eg, n, 1)
    except AttributeError as e: print("set", n, e)
    try: delattr(eg, n)
    except AttributeError as e: print("del", n, e)
eg = ExceptionGroup("msg", [ValueError()]); eg.args = (); print(repr(eg)); eg.args = (1,); print(repr(eg))
class Bad(list):
    def __repr__(self): return None
try: ExceptionGroup("t", Bad([ValueError()]))
except TypeError as e: print(e)
class R:
    def __len__(self): return 1
    def __getitem__(self, i):
        if i == 0: return ValueError(1)
        raise IndexError
    def __repr__(self): return None
try: ExceptionGroup("t", R())
except TypeError as e: print(e)
class C(ExceptionGroup):
    message = "cls"
c = C("m", [ValueError()]); print(c.message); c.message = "x"; print(c.message, c.exceptions)
print(type(eg).__repr__, "message" in dir(eg), hasattr(eg, "message"))
e2 = eg.derive([KeyError(1)]); print(repr(e2), e2.message)
m, r = ExceptionGroup("x", [ValueError(1), TypeError(2)]).split(ValueError); print(repr(m), repr(r))
''',
              '''MyEG('test', [ValueError(1), TypeError(2)])
MyEG('test', [ValueError(1), TypeError(2)]) ('test', []) {}
BaseExceptionGroup('test', (ValueError(1), KeyboardInterrupt(2)))
ExceptionGroup('t', Seq([ValueError(1)])) (ValueError(1),) t (1 sub-exception)
TypeError second argument (exceptions) must be a sequence
TypeError second argument (exceptions) must be a sequence
ValueError Item 0 of second argument (exceptions) is not an exception
TypeError second argument (exceptions) must be a sequence
set message readonly attribute
del message readonly attribute
set exceptions readonly attribute
del exceptions readonly attribute
ExceptionGroup('msg', (ValueError(),))
ExceptionGroup('msg', (ValueError(),))
R.__repr__() must return a str, not NoneType
cls
x (ValueError(),)
<slot wrapper '__repr__' of 'BaseExceptionGroup' objects> True True
ExceptionGroup('msg', [KeyError(1)]) msg
ExceptionGroup('x', [ValueError(1)]) ExceptionGroup('x', [TypeError(2)])
''')

check_program('e = ValueError(1)\nfor n in ("args", "__traceback__", "__context__", "__cause__", "__suppress_context__"):\n    try: delattr(e, n); print("deleted", n)\n    except Exception as x: print(n, type(x).__name__, x)\ns = SyntaxError("m", ("f", 1, 2, "t")); del s.lineno; print(s.lineno, s.__dict__)\no = OSError(2, "x")\ntry: del o.characters_written\nexcept Exception as x: print(type(x).__name__, x)\ntry: o.characters_written\nexcept Exception as x: print(type(x).__name__, x)\ntry: o.characters_written = "a"\nexcept Exception as x: print(type(x).__name__, x)\no.characters_written = 3; print(o.characters_written); del o.characters_written\nprint(hasattr(o, "characters_written"))\ndel o.errno; print(o.errno)\nst = StopIteration(5); del st.value; print(st.value)\ne = ValueError(1); e.x = 2; print(e.__dict__, e.__reduce__())\nprint(ValueError(1).__reduce__())\nu = UnicodeEncodeError("ascii", "aé", 1, 2, "bad"); print(u, u.encoding, u.object, u.start, u.end, u.reason, u.args)\nprint(UnicodeEncodeError("ascii", "aሴ\\U00012345", 1, 3, "r"), UnicodeEncodeError("ascii", "aሴ", 1, 2, "r"))\nprint(UnicodeDecodeError("utf-8", b"\\xff\\xfe", 0, 1, "r"), UnicodeDecodeError("utf-8", b"\\xff\\xfe", 0, 2, "r"))\nprint(UnicodeTranslateError("ab", 0, 1, "r"), UnicodeTranslateError("ab", 0, 2, "r").encoding)\ntry: b"\\xff".decode("utf-8")\nexcept UnicodeDecodeError as x: print(x.encoding, x.object, x.start, x.end, x.reason, x.args)\ntry: "é".encode("ascii")\nexcept UnicodeEncodeError as x: print(x.encoding, x.object, x.start, x.end, x.reason, x.args)\nfor bad in ((1, "a", 0, 1, "r"), ("a",), ()):\n    try: print(UnicodeEncodeError(*bad))\n    except TypeError as x: print(x)\nprint(str(UnicodeError("x")), UnicodeError().__dict__)\ne = SystemExit(3); print(e.code, e.__dict__); e = ImportError("m", name="n"); print(e.msg, e.name, e.path, e.__dict__)\ne = AttributeError("m", name="n", obj=1); print(e.name, e.obj, e.__dict__); print(NameError("x", name="y").name)\n',
              "args TypeError args may not be deleted\n__traceback__ TypeError __traceback__ may not be deleted\n__context__ TypeError __context__ may not be deleted\n__cause__ TypeError __cause__ may not be deleted\n__suppress_context__ TypeError can't delete numeric/char attribute\nNone {}\nAttributeError characters_written\nAttributeError characters_written\nTypeError 'str' object cannot be interpreted as an integer\n3\nFalse\nNone\nNone\n{'x': 2} (<class 'ValueError'>, (1,), {'x': 2})\n(<class 'ValueError'>, (1,))\n'ascii' codec can't encode character '\\xe9' in position 1: bad ascii aé 1 2 bad ('ascii', 'aé', 1, 2, 'bad')\n'ascii' codec can't encode characters in position 1-2: r 'ascii' codec can't encode character '\\u1234' in position 1: r\n'utf-8' codec can't decode byte 0xff in position 0: r 'utf-8' codec can't decode bytes in position 0-1: r\ncan't translate character '\\x61' in position 0: r None\nutf-8 b'\\xff' 0 1 invalid start byte ('utf-8', b'\\xff', 0, 1, 'invalid start byte')\nascii é 0 1 ordinal not in range(128) ('ascii', 'é', 0, 1, 'ordinal not in range(128)')\nargument 1 must be str, not int\nfunction takes exactly 5 arguments (1 given)\nfunction takes exactly 5 arguments (0 given)\nx {}\n3 {}\nm n None {}\nn 1 {}\ny\n")

check_program('''print(OSError(2, "x", "f").__reduce__(), OSError(2, "x", "f", None, "g").__reduce__())
print(ImportError("m", name="n").__reduce__(), ImportError("m").__reduce__())
print(AttributeError("m").__reduce__(), AttributeError("m", name="n", obj=1).__reduce__(), AttributeError("q").__getstate__())
e = ValueError(1); e.__dict__; print(e.__reduce__())
e = ValueError(1); e.__setstate__({"x": 1, "args": (2,)}); print(e.x, e.args, e.__dict__)
try: e.__setstate__(5)
except TypeError as x: print(x)
e.__setstate__(None)
e = KeyError("k"); print(str(e), repr(e), e.args)
try: raise ValueError(1) from KeyError(2)
except ValueError as e: print(repr(e.__cause__), e.__suppress_context__, e.__dict__)
''',
              '''(<class 'FileNotFoundError'>, (2, 'x', 'f')) (<class 'FileNotFoundError'>, (2, 'x', 'f', None, 'g'))
(<class 'ImportError'>, ('m',), {'name': 'n'}) (<class 'ImportError'>, ('m',))
(<class 'AttributeError'>, ('m',), {'args': ('m',)}) (<class 'AttributeError'>, ('m',), {'name': 'n', 'args': ('m',)}) {'args': ('q',)}
(<class 'ValueError'>, (1,), {})
1 (2,) {'x': 1}
state is not a dictionary
'k' KeyError('k') ('k',)
KeyError(2) True {}
''')

check_program('for cls, args in ((UnicodeDecodeError, ("u", "s", 0, 1, "r")), (UnicodeDecodeError, ("u", bytearray(b"ab"), 0, 1, "r")),\n                  (UnicodeEncodeError, ("u", "s", "0", 1, "r")),\n                  (UnicodeEncodeError, ("u", "s", 0, 1, 5)), (UnicodeTranslateError, ("s", 0, 1)), (UnicodeTranslateError, (1, 0, 1, "r")),\n                  (UnicodeEncodeError, ("u", "s", 2**70, 1, "r")), (UnicodeEncodeError, ("u", "abc", 5, 9, "r")), (UnicodeEncodeError, ("u", "abc", -1, 1, "r"))):\n    try:\n        e = cls(*args); print(repr(e), "|", str(e), "|", e.object, e.start, e.end)\n    except Exception as x: print(type(x).__name__, x)\ne = UnicodeEncodeError("u", "abc", 0, 1, "r"); e.reason = 5; e.encoding = 3; print(str(e))\ne.start = 1; e.end = 3; print(str(e))\ntry: e.start = "x"\nexcept TypeError as x: print(x)\nprint(str(UnicodeError("x")), str(UnicodeError()), repr(UnicodeEncodeError("u", "abc", 0, 1, "r")))\nclass U(UnicodeDecodeError): pass\nprint(str(U("utf-8", b"\\x80", 0, 1, "bad")))\n',
              "TypeError a bytes-like object is required, not 'str'\nUnicodeDecodeError('u', bytearray(b'ab'), 0, 1, 'r') | 'u' codec can't decode byte 0x61 in position 0: r | b'ab' 0 1\nTypeError 'str' object cannot be interpreted as an integer\nTypeError argument 5 must be str, not int\nTypeError function takes exactly 4 arguments (3 given)\nTypeError argument 1 must be str, not int\nOverflowError Python int too large to convert to C ssize_t\nUnicodeEncodeError('u', 'abc', 5, 9, 'r') | 'u' codec can't encode characters in position 5-8: r | abc 5 9\nUnicodeEncodeError('u', 'abc', -1, 1, 'r') | 'u' codec can't encode characters in position -1-0: r | abc -1 1\n'3' codec can't encode character '\\x61' in position 0: 5\n'3' codec can't encode characters in position 1-2: 5\nan integer is required\nx  UnicodeEncodeError('u', 'abc', 0, 1, 'r')\n'utf-8' codec can't decode byte 0x80 in position 0: bad\n")

check_program('''d = {}
for i in range(3000):
    d = {1: d}
try: repr(d)
except RecursionError as e: print("RecursionError", e)
l = []
for i in range(3000): l = [l]
try: repr(l)
except RecursionError as e: print("RecursionError")
class B:
    def __repr__(self): raise ValueError("x")
x = [1, B()]
try: repr(x)
except ValueError: print("ok", repr([x[0]]), x[:1])
y = [1]; y.append(y); print(y, (y,), {1: y})
''',
              '''ok [1] [1]
[1, [...]] ([1, [...]],) {1: [1, [...]]}
''')

check_program('''try:
    pass
else:
    pass
''',
              '''SyntaxError: expected 'except' or 'finally' block (<program>, line 3)
''')
