# spec: PLS-315 12.5
# description: Programs on f-strings, each with the output CPython 3.15 gives.
from harness import *

check_program('from __future__ import annotations\ndef f(x: f(y for y in z), y: f((y for y in z), 1), z: 1 .real, w: f"a{b!r:>{w}}c{{\'\\"", v: lambda a, /, b=1, *, c, **k: 0,\n      u: lambda *a, b: 0, t: -(-1) ** -2 ** 3, s: (a if b else c) if d else e, r: not not a, q: (a, ), p: (), o: {*()},\n      n: a[1:2, ::3, :], m: a[1,], l: a[(1, 2)], k: a[*b], j: [x for x in y if z if w], i: {k: v for k, v in d},\n      g: 0x10 + 1_000 + 1e3 + 1e1000 + 1j + 1e1000j + 0.5, ff: \'a\' "b" \'c\\n\\x00ሴ\', ee: b\'x\\\'"\', dd: ...,\n      cc: a < b < c, bb: a or b and c or not d, aa: (a or b) and c, ab: a ** -b, ac: (-a) ** b, ad: (a + b) * c - d / e // f % g @ h,\n      ae: a << b | c ^ d & e, af: f(*a, *b, x=1, **k), ai: a.b.c[d](e), aj: (1).real, ak: 1.5.real, al: (lambda: 1)(),\n      an: {**a, \'b\': 1}, ao: [*a, *b], ap: f\'{x=}\', aq: f\'{"a"}\', ar: f\'{a:{b}}\', at: \'it\\\'s\', au: "a\'b\\"c", av: -1, aw: ~a + +b, ax: x if y else lambda: z,\n      ay: (not a) + b, az: not a + b, ba: a is not b, bc: a not in b, bd: [] , be: {}, bf: (a, *b), bg: f(a)(b), bh: a[b][c]):\n    pass\nfor k, v in f.__annotations__.items(): print(k, v)\n',
              'x f(y for y in z)\ny f((y for y in z), 1)\nz 1 .real\nw f\'a{b!r:>{w}}c{{\\\'"\'\nv lambda a, /, b=1, *, c, **k: 0\nu lambda*a, b: 0\nt -(-1) ** (-2 ** 3)\ns (a if b else c) if d else e\nr not not a\nq (a,)\np ()\no {*()}\nn a[1:2, ::3, :]\nm a[1,]\nl a[1, 2]\nk a[*b,]\nj [x for x in y if z if w]\ni {k: v for k, v in d}\ng 16 + 1000 + 1000.0 + 1e309 + 1j + 1e309j + 0.5\nff \'abc\\n\\x00ሴ\'\nee b\'x\\\'"\'\ndd ...\ncc a < b < c\nbb a or b and c or not d\naa (a or b) and c\nab a ** (-b)\nac (-a) ** b\nad (a + b) * c - d / e // f % g @ h\nae a << b | c ^ d & e\naf f(*a, *b, x=1, **k)\nai a.b.c[d](e)\naj 1 .real\nak 1.5.real\nal (lambda: 1)()\nan {**a, \'b\': 1}\nao [*a, *b]\nap f\'x={x!r}\'\naq f"{\'a\'}"\nar f\'{a:{b}}\'\nat "it\'s"\nau \'a\\\'b"c\'\nav -1\naw ~a + +b\nax x if y else lambda: z\nay (not a) + b\naz not a + b\nba a is not b\nbc a not in b\nbd []\nbe {}\nbf (a, *b)\nbg f(a)(b)\nbh a[b][c]\n')

check_program('''x = 3; print(f'hello {x}, {x*2=}, {x!r}')
''',
              '''hello 3, x*2=6, 3
''')

check_program('''print(f'{12:04d} {3.14159:.2f} {255:#06x} {0.125:.1%}')
''',
              '''0012 3.14 0x00ff 12.5%
''')

check_program('''print(f'{3:{4}}', f'{-42:=8}', f'{42:+08}', f'{255:#08X}')
''',
              '''   3 -     42 +0000042 0X0000FF
''')

check_program('print(ascii(\'é🙂\'), f\'{"é🙂"!a}\', \'\\u00e9\', \'\\U0001f642\', \'\\377\', r\'\\n\', u\'hi\')\n',
              "'\\xe9\\U0001f642' '\\xe9\\U0001f642' é 🙂 ÿ \\n hi\n")

check_program('''print('a' f'{1}' 'b', f'', f'{{{1}}}', f'{1 == 2}', f'{1 != 2}')
''',
              '''a1b  {1} False True
''')

check_program('''print(f'{f"{1+2}"!r}', f'{ {"x": 1}["x"] }')
''',
              ''''3' 1
''')

check_program('''print(f'{2 # a field comment
}', f'{(x := 3)} {x}', f'{ x = }')
''',
              '''2 3 3  x = 3
''')

check_program('''events = []
class Value:
    def __str__(self):
        events.append('convert')
        return 'value'
    def __format__(self, spec):
        events.append(('format', spec))
        return 'formatted'
def spec():
    events.append('spec')
    return ''
print(f'{Value()!s:{spec()}}', events)
events = []
print(f'{Value():{spec()}}', events)
''',
              '''value ['convert', 'spec']
formatted ['spec', ('format', '')]
''')

check_program('''class C:
    __x = 8
    def show(self):
        return f'{self.__x} {self.__x=}'
print(C().show())
''',
              '''8 self.__x=8
''')

check_program('''g = {'x': 5}
l = {'x': 6}
print(eval('x + 1', g), eval('x + 1', g, l))
exec('y = x + 2', g, l)
print(l['y'], 'y' in g, '__builtins__' in g)
exec('def f(): return x', g, l)
print(l['f'](), l['f'].__globals__ is g)
exec('global z; z = x', g, l)
print(g['z'], 'z' in l)
''',
              '''6 7
8 False True
5 True
6 False
''')

check_program('''def f():
    x = 7
    print(eval('x + 1'))
    exec('x = 9')
    print(x, eval('x'))
f()
g = {'__builtins__': {'answer': 42}}
print(eval('answer', g))
exec('def f(): return answer', g)
print(g['f']())
''',
              '''8
7 7
42
42
''')

check_program('''a = {1}; b = a; a |= {2}; print(b, a is b)
x = [1]; y = x; x *= 2; print(y)
d = {1: 2}; e = d; d |= {3: 4}; print(e)
ba = bytearray(b"a"); bb = ba; ba += b"b"; print(bb)
class L(list): pass
l = L([1]); m = l; l *= 3; print(m, type(l).__name__)
class S(set): pass
s = S([1]); t = s; s |= {5}; print(sorted(t), type(s).__name__)
class D(dict): pass
q = D(a=1); r = q; q |= {"b": 2}; print(r, type(q).__name__)
class MyInt(int): pass
i = MyInt(3); i += 1; print(i, type(i).__name__)
class T(tuple): pass
print(T([1, 2]) + T([3]), T() == (), T("ab"), type(T("ab")[0:1]).__name__)
class Str(str):
    def __str__(self): return "custom"
print(str(Str("x")), repr(Str("x")), f"{Str('x')}", "%s" % Str("x"), Str("x") + "y")
class R(int):
    def __repr__(self): return "R!"
print(str(R(1)), repr(R(1)), f"{R(1)}", [R(1)])
class Init(list):
    def __init__(self, n):
        super().__init__(range(n))
        self.n = n
v = Init(3); print(v, v.n, v.__dict__, len(v))
class Slots(list):
    pass
w = Slots(); w.extra = 1; print(w, w.extra, vars(w))
print(MyInt.__base__, issubclass(MyInt, int), MyInt(5).__class__.__name__, type(MyInt(5)) is MyInt)
class N(int):
    def __new__(cls, v): return super().__new__(cls, v * 10)
print(N(4), N(4) + 0)
class K(dict):
    def __getitem__(self, k): return "over"
k = K(a=1); print(k["a"], k.get("a"), dict(k), list(k))
class Keyed(dict):
    def keys(self): return ["a"]
print(dict(Keyed(a=1, b=2)))
print(sorted([MyInt(3), 1, MyInt(2)]), max(MyInt(3), 9), sum([MyInt(1), MyInt(2)]))
print(MyInt(3) in {3}, Str("x") in {"x": 1}, {MyInt(3): "a"}, MyInt(10) // 3, MyInt(10) / 4, MyInt(2) ** 10, 5 - MyInt(2), [1] * MyInt(2))
''',
              '''{1, 2} True
[1, 1]
{1: 2, 3: 4}
bytearray(b'ab')
[1, 1, 1] L
[1, 5] S
{'a': 1, 'b': 2} D
4 int
(1, 2, 3) True ('a', 'b') tuple
custom 'x' custom custom xy
R! R! R! [R!]
[0, 1, 2] 3 {'n': 3} 3
[] 1 {'extra': 1}
<class 'int'> True MyInt True
40 40
over 1 {'a': 1} ['a']
{'a': 1, 'b': 2}
[1, 2, 3] 9 3
True True {3: 'a'} 3 2.5 1024 3 [1, 1]
''')

check_program('''f'{!r}'
''',
              '''SyntaxError: f-string: valid expression required before '!' (<program>, line 1)
''')

check_program('''f'{1!q}'
''',
              '''SyntaxError: f-string: invalid conversion character 'q': expected 's', 'r', or 'a' (<program>, line 1)
''')

check_program('''f'}'
''',
              '''SyntaxError: f-string: single '}' is not allowed (<program>, line 1)
''')

check_program('''f'{1'
''',
              '''SyntaxError: f-string: expecting '}' (<program>, line 1)
''')

check_program('''class C:
    def __format__(self, spec): return 1
f'{C()}'
''',
              '''TypeError: C.__format__() must return a str, not int
''')
