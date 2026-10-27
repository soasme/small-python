# spec: PLS-315 27.2
# description: Programs on generators, each with the output CPython 3.15 gives.
from harness import *

check_program('''def g():
    yield f'a{(yield 1)}b{(yield 2)}'
    yield f'{12:{(yield 3)}}'
x = g()
print(next(x), x.send(4), x.send(5))
print(next(x), x.send('04d'))
''',
              '''1 2 a4b5
3 0012
''')

check_program('class Point:\n    __match_args__ = ("x", "y")\n    def __init__(self, x, y): self.x = x; self.y = y\nclass Color:\n    RED = 1\n    GREEN = 2\ndef describe(v):\n    match v:\n        case None: return "none"\n        case True: return "true"\n        case 0 | 1 as small: return f"small {small}"\n        case -3.5: return "neg float"\n        case 1+2j: return "complex"\n        case "hi" | b"hi": return "greeting"\n        case Color.RED: return "red"\n        case Point(0, 0): return "origin"\n        case Point(x=0, y=y): return f"y-axis {y}"\n        case Point(x, y) if x == y: return f"diag {x}"\n        case Point(): return "point"\n        case [x, y, *rest]: return f"seq {x} {y} {rest}"\n        case [x]: return f"one {x}"\n        case (): return "empty"\n        case {"k": v, **kw}: return f"map {v} {kw}"\n        case {}: return "anymap"\n        case int(n) if n > 100: return f"big {n}"\n        case str() as s: return f"str {s}"\n        case float(f): return f"float {f}"\n        case _: return "other"\nfor v in [None, True, 0, 1, False, -3.5, 1+2j, "hi", b"hi", Color.RED, 2, Point(0, 0), Point(0, 5), Point(3, 3), Point(1, 2),\n          [1, 2], [1, 2, 3, 4], (9,), [], (), {"k": 1, "z": 2}, {"a": 1}, 500, "s", 2.5, range(3), "ab", b"x", bytearray(b"ab")]:\n    print(describe(v))\nmatch [1, [2, 3]]:\n    case [a, [b, *c]]:\n        print(a, b, c)\nx = 5\nmatch x:\n    case 1: pass\n    case y: print("captured", y)\nmatch w := x,:\n    case (5,): print("walrus subject", w)\nmatch *[x], w := 3:\n    case (5, 3): print("starred subject", w)\ndef gen(items):\n    for item in items:\n        match item:\n            case [k, v] if (yield k):\n                yield ("guard", v)\n            case [k, v]:\n                yield ("plain", k, v)\n            case _:\n                yield "skip"\ng = gen([[1, 2], 3, [4, 5]])\nprint(next(g), g.send(True), next(g), next(g), g.send(False))\nfor bad in ["match x:\\n case _: pass\\n case 1: pass", "match x:\\n case a | b: pass", "match x:\\n case [a, a]: pass",\n            "match x:\\n case {**_}: pass", "match x:\\n case [*a, *b]: pass", "match x:\\n case 1 + 2: pass",\n            "match x:\\n case a: pass\\n case 2: pass", "match x:\\n case Point(x=1, x=2): pass"]:\n    try: compile(bad, "<s>", "exec"); print("ok")\n    except SyntaxError as e: print("SyntaxError", e.msg)\nclass C:\n    __match_args__ = ("a",)\n    a = 1\nfor code in ["match 1:\\n case int(1, 2): pass", "match C():\\n case C(1, 2): pass", "match 1:\\n case len(): pass", "match {\'a\':1}:\\n case {\'a\': 1, \'a\': 2}: pass"]:\n    try: exec(code); print("ok")\n    except Exception as e: print(type(e).__name__, e)\nmatch = 3; case = 4; print(match, case)\ndef f(match): return match\nprint(f(2), [match for match in [7]])\nmatch = {"a": 1}\nmatch["a"] = 2\nprint(match)\n',
              '''none
true
small 0
small 1
small False
neg float
complex
greeting
greeting
small 1
other
origin
y-axis 5
diag 3
point
seq 1 2 []
seq 1 2 [3, 4]
one 9
empty
empty
map 1 {'z': 2}
anymap
big 500
str s
float 2.5
seq 0 1 [2]
str ab
other
other
1 2 [3]
captured 5
walrus subject 5
starred subject 3
1 ('guard', 2) skip 4 ('plain', 4, 5)
SyntaxError wildcard makes remaining patterns unreachable
SyntaxError name capture 'a' makes remaining patterns unreachable
SyntaxError multiple assignments to name 'a' in pattern
SyntaxError invalid syntax
SyntaxError multiple starred names in sequence pattern
SyntaxError imaginary number required in complex literal
SyntaxError name capture 'a' makes remaining patterns unreachable
SyntaxError attribute name repeated in class pattern: x
TypeError int() accepts 1 positional sub-pattern (2 given)
TypeError C() accepts 1 positional sub-pattern (2 given)
TypeError class pattern must refer to a class
SyntaxError mapping pattern checks duplicate key ('a') (<string>, line 2)
3 4
2 [7]
{'a': 2}
''')

check_program('''def f(): yield from [], []
''',
              '''SyntaxError: invalid syntax (<program>, line 1)
''')

check_program('''def f(): x = yield from [], []
''',
              '''SyntaxError: invalid syntax (<program>, line 1)
''')

check_program('''def f(): return yield 1
''',
              '''SyntaxError: invalid syntax (<program>, line 1)
''')

check_program('''def f(): yield yield 1
''',
              '''SyntaxError: invalid syntax (<program>, line 1)
''')

check_program('''def f(): print(yield 1)
''',
              '''SyntaxError: invalid syntax (<program>, line 1)
''')

check_program('''def f(): assert yield 1
''',
              '''SyntaxError: invalid syntax (<program>, line 1)
''')

check_program('''yield 1
''',
              '''SyntaxError: 'yield' outside function (<program>, line 1)
''')

check_program('''yield from []
''',
              '''SyntaxError: 'yield from' outside function (<program>, line 1)
''')

check_program('''def f(): return [(yield i) for i in []]
''',
              '''SyntaxError: 'yield' inside list comprehension (<program>, line 1)
''')

check_program('''def f(): return (i for i in [] if (yield 1))
''',
              '''SyntaxError: 'yield' inside generator expression (<program>, line 1)
''')

check_program('''def f(): return {i: (yield i) for i in []}
''',
              '''SyntaxError: 'yield' inside dict comprehension (<program>, line 1)
''')

check_program('''class Items:
    def __iter__(self): print('iter'); yield 3; yield 1
class Reverse:
    def __bool__(self): print('reverse'); return True
def key(x): print('key', x); return x
print(sorted(Items(), key=key, reverse=Reverse()))
for reverse in [None, 1.0, [], [1]]:
    print(sorted([3, 1], reverse=reverse))
try: sorted(Items(), unknown=1)
except TypeError: print('unexpected keyword')
''',
              '''iter
reverse
key 3
key 1
[3, 1]
[1, 3]
[3, 1]
[1, 3]
[3, 1]
iter
unexpected keyword
''')
