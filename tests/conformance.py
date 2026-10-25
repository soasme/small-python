"""Differential checks for the implemented subset, not CPython's test suite."""

from pathlib import Path
import random
import math
import struct
import subprocess
import sys
import tempfile
import textwrap

ENGINE = str(Path(sys.argv[1]).resolve())
CASES = [
    "print('Hello, world!')",
    "print(None, True, False, bool([]), bool([0]))",
    "print(1 + 2 * 3, (1 + 2) * 3, -2**2, (-2)**2, 2**-2, 2**3**2)",
    "print(-7 // 3, -7 % 3, 7 // -3, 7 % -3, -7 // -3, -7 % -3)",
    "print(0xff, 0o17, 0b1010, 1_000, 1.25e2)",
    "print(1 << 5, -9 >> 2, 15 & 6, 15 | 16, 9 ^ 3, ~7)",
    "print(1 < 2 < 3, 1 < 2 > 3, 3 > 2 >= 2, 1 == True, None is None)",
    "print(0 and missing, 4 or missing, not 1 == 2, not [] and True)",
    "print(1 if True else missing, missing if False else 2)",
    "print('a' 'b', 'ab' * 3, 3 * 'x', 'a' + 'b', len('hé🙂'), 'hé🙂'[2])",
    "print('a\\nb', 'c\\td', 'quote: \\'', '\\\\', '\\x41')",
    "print('''hello\nworld''')",
    "print(len('a\\x00b'), 'a\\x00b'[1] == '\\x00', 'b' in 'a\\x00b')",
    "print('bc' in 'abcd', 'xy' not in 'abcd', '' in '', 'a' < 'b')",
    "print([1, 2] + [3], [1] * 3, (1, 2) + (3,), (1,) * 2)",
    "print([1, 2] == [1, 2], [1] != [2], (1,) != [1], [] == [])",
    "a = [1, 2, 3]; a[-1] = 7; a.append(9); print(a, a.pop(), a.pop(0), a)",
    "a = []; a.append(a); print(a)",
    "a = []; b = a; a += [1, 2]; print(a, b, a is b)",
    "a = [1, 2]; a += a; print(a)",
    "d = {'a': 1, 'b': 2}; d['c'] = 3; d['a'] += 4; print(d, d['a'])",
    "d = {1: 'first', True: 'second'}; print(d, len(d), 1 in d)",
    "d = {'a': 1, 'b': 2}; print(d.get('x'), d.get('x', 8), list(d.keys()), list(d.values()), list(d.items()))",
    "d = {}; d['self'] = d; print(d)",
    "print(list(range(5)), list(range(5, -2, -2)), len(range(10, 0, -3)), bool(range(0)))",
    "print(tuple(range(3)), list('abc'), list((1, 2)), list({'x': 3}))",
    "print(sum(range(10)), sum([1, 2], 10), min([3, 1, 2]), max(1, 5, 3))",
    "print(all([]), any([]), all([1, 2]), any([0, 3]), all([0, 1]))",
    "print(int(' 42 '), int(-1.9), float('2.5'), str(42), repr([1]), abs(-3), abs(-2.5))",
    "print(int(), float(), bool(), str(), list(), tuple(), dict())",
    "x = 5; x += 2; x *= 3; x -= 1; x %= 6; x /= 2; print(x)",
    """
    if False:
        print('no')
    elif 2 > 1:
        print('yes')
    else:
        print('no')
    """,
    """
    x = 0
    while x < 5:
        x += 1
        if x == 2:
            continue
        print(x)
    else:
        print('done')
    """,
    """
    for x in range(5):
        if x == 3:
            break
        print(x)
    else:
        print('bad')
    for x in []:
        print('bad')
    else:
        print('empty')
    """,
    """
    for x in range(3):
        for y in range(3):
            if y == 1:
                break
            print(x, y)
    """,
    """
    def fib(n):
        if n < 2:
            return n
        return fib(n - 1) + fib(n - 2)
    print(fib(12))
    """,
    """
    def make(x):
        def add(y):
            return x + y
        return add
    a = make(2)
    b = make(3)
    print(a(4), b(4), a(7))
    """,
    """
    def f(n):
        for x in range(n):
            if x == 3:
                return x
        return -1
    print(f(5), f(2))
    """,
    "def nothing(): pass\nprint(nothing())",
    """
    calls = []
    def middle():
        calls.append(1)
        return 2
    print(1 < middle() < 3, calls)
    print(4 < middle() < missing, calls)
    """,
    """
    calls = []
    a = [2]
    def index():
        calls.append('index')
        return 0
    def rhs():
        calls.append('rhs')
        return 3
    a[index()] += rhs()
    print(a, calls)
    calls = []
    a[index()] = rhs()
    print(a, calls)
    """,
    "x = (\n    1 +\n    2\n)\nprint(x)",
    "x = 1 + \\\n    2\nprint(x)",
    "# comment\n\nif True:\n    # comment\n    print(42)\n\n# last",
    "if True: print(1); print(2)\nprint(3)",
    "print(__name__)",
    "print(0.1, 0.3, 1e-4, 1e-5, 1e15, 1e16, -0.0, 1.2345678901234567)",
    "print(1.0 // 0.1, 1.0 % 0.1, -1.0 // 0.1, -1.0 % 0.1)",
    "print(9007199254740993 == 9007199254740992.0, 9007199254740993 > 9007199254740992.0, 9223372036854775807 < 9223372036854775808.0)",
    "n = float('nan'); print(n == n, n != n, n < 0, [n] == [n])",
    "print({'a': [1], 'b': 2} == {'b': 2, 'a': [1]}, {} == {}, {} != {'a': 1})",
    "print(0x_FF, 0b_101, 0o_17, 1_000.5_5)",
    "if True:\n    x = (\n        1 + 2\n    )\n    print(x)\nprint(4)",
]
CASES += [
    "a, (b, *c), d = [1, range(2, 6), 7]; print(a, b, c, d)",
    "a = b = []; a.append(1); print(a is b, b); a, b = b, a; print(a is b)",
    "i = 0; a = [0, 0]; i, a[i] = 1, 5; print(i, a)",
    "x = 50; print([(x, y) for x in range(4) if x for y in range(x) if y]); print(x)",
    "print({k: v for k, v in zip('ab', [1, 2])}); print(sorted({i % 3 for i in range(10)}))",
    "print(sorted({1, *range(4)}), {**{'a': 1}, 'b': 2, **{'a': 3}})",
    "print(True & False, True | False, True ^ True, True & 3)",
    "it = iter([1]); print(next(it), next(it, 42), next(it, 43)); print(iter(it) is it)",
    "it = iter(range(10)); print(list(zip(it, it)), next(it, None)); print(list(enumerate('ab', 3)))",
    "print(list(reversed([1, 2, 3])), list(reversed('hé🙂')), sorted([(2, 0), (1, 2), (1, 1)]))",
    """
    def f(a, /, b=2, *args, c=3, **kw):
        return a, b, args, c, kw
    print(f(1, 4, 5, 6, c=7, a=8, d=9))
    print(f(*(1,), **{'b': 4, 'c': 5}))
    def remember(x, items=[]):
        items.append(x)
        return items
    print(remember(1), remember(2))
    print((lambda a, *, b=2: a+b)(3, b=4))
    """,
    """
    log = []
    def mark(x):
        log.append(x)
        return x
    def f(a, b):
        return a, b
    print(f(b=mark(2), *[mark(1)]), log)
    """,
    """
    class Base:
        value = 4
        def f(self, n=1):
            return self.value + n
    class Child(Base):
        def __init__(self, value):
            self.value = value
        def __call__(self, x):
            return self.f(x)
    a = Child(value=10)
    method = a.f
    a.value += 2
    print(method(), a(3), Base.value)
    """,
    """
    x = 3
    class C:
        x = 4
        def f(self):
            return x
    print(C.x, C().f())
    """,
    """
    class Counter:
        def __init__(self, n):
            self.n = n
        def __iter__(self):
            return self
        def __next__(self):
            if not self.n:
                raise StopIteration
            self.n -= 1
            return self.n
    it = Counter(4)
    print(iter(it) is it, next(it), list(it), next(it, 42))
    print(sum(Counter(5)), any(Counter(1)), all(Counter(2)))
    """,
    """
    class Problem(ValueError):
        pass
    log = []
    def f():
        try:
            try:
                raise Problem('detail')
            except LookupError:
                log.append('wrong')
            except (TypeError, ValueError) as error:
                log.append(error.args[0])
                raise
            finally:
                log.append('inner finally')
        except Problem:
            return 42
        finally:
            log.append('outer finally')
    print(f(), log)
    """,
    """
    def f():
        try:
            return 1
        finally:
            return 2
    def g():
        try:
            1 / 0
        finally:
            return 3
    print(f(), g())
    for i in range(3):
        try:
            if i == 0:
                continue
            break
        finally:
            print(i)
    """,
    """
    try:
        1 / 0
    except ArithmeticError as e:
        print('caught')
    else:
        print('wrong')
    try:
        e
    except NameError:
        print('deleted')
    """,
    """
    def make(n):
        return ((i, j) for i in range(n) for j in range(i) if j % 2 == 0)
    g = make(4)
    print(next(g), list(g), list(g))
    x = 3
    g = (i * x for i in range(x))
    x = 4
    print(list(g))
    """,
    """
    def f():
        g = ((saved := i*i) for i in range(3))
        print(next(g), saved, list(g), saved)
        return [(last := x) for x in range(3)], last
    print(f())
    """,
    """
    def stop():
        raise StopIteration
    g = (stop() for x in range(1))
    try:
        next(g)
    except RuntimeError:
        print('converted')
    print(list(g))
    """,
]
ERRORS = [
    ("1 / 0", "ZeroDivisionError"),
    ("1 // 0", "ZeroDivisionError"),
    ("1 % 0", "ZeroDivisionError"),
    ("0 ** -1", "ZeroDivisionError"),
    ("missing", "NameError"),
    ("[1][2]", "IndexError"),
    ("{}['x']", "KeyError"),
    ("{}[[]]", "TypeError"),
    ("{[]: 1}", "TypeError"),
    ("1 + 'x'", "TypeError"),
    ("1(2)", "TypeError"),
    ("len(1)", "TypeError"),
    ("range(1, 2, 0)", "ValueError"),
    ("1 << -1", "ValueError"),
    ("[].pop()", "IndexError"),
    ("assert False, 'oops'", "AssertionError"),
    ("def f(a): return a\nf()", "TypeError"),
    ("x = 1\ndef f():\n    print(x)\n    x = 2\nf()", "UnboundLocalError"),
    ("def f():\n    if False:\n        x = 1\n    return x\nf()", "UnboundLocalError"),
    ("return 1", "SyntaxError"),
    ("break", "SyntaxError"),
    ("continue", "SyntaxError"),
    ("if:\n pass", "SyntaxError"),
    ("def f(a, a): pass", "SyntaxError"),
    ("(1]", "SyntaxError"),
    ("'unterminated", "SyntaxError"),
    ("1 = 2", "SyntaxError"),
    ("1e+", "SyntaxError"),
    ("1__0", "SyntaxError"),
    ("0123", "SyntaxError"),
    ("1_e2", "SyntaxError"),
    ("1e_2", "SyntaxError"),
    ("1 + not 2", "SyntaxError"),
    ("[] in {}", "TypeError"),
    ("(*x), y = 1, 2", "SyntaxError"),
    ("[x := 1 for x in range(3)]", "SyntaxError"),
    ("[x for x in (y := range(3))]", "SyntaxError"),
    ("class C:\n    x = [(y := 1) for z in range(3)]", "SyntaxError"),
    ("def f(a): pass\nf(1, a=2)", "TypeError"),
    ("def f(*, a): pass\nf(1)", "TypeError"),
    ("def f(a, /): pass\nf(a=1)", "TypeError"),
    ("def f(**kw): pass\nf(**{1: 2})", "TypeError"),
    ("def f(**kw): pass\nf(a=1, **{'a': 2})", "TypeError"),
    ("try:\n    pass\nelse:\n    pass", "SyntaxError"),
    ("try:\n    1 / 0\nexcept 42:\n    pass", "TypeError"),
]


def run(command, source, cwd=None):
    return subprocess.run(
        [*command, "-c", source], capture_output=True, text=True, timeout=10, cwd=cwd
    )


def check(source, error=None):
    source = textwrap.dedent(source).strip() + "\n"
    expected = run([sys.executable, "-I"], source)
    actual = run([ENGINE], source)
    if error:
        ok = expected.returncode != 0 and actual.returncode == 1 and error + ":" in actual.stderr
    else:
        ok = expected.returncode == actual.returncode == 0 and actual.stdout == expected.stdout
    if not ok:
        raise AssertionError(
            f"Source:\n{source}\nCPython ({expected.returncode}):\n{expected.stdout}{expected.stderr}"
            f"\nspy ({actual.returncode}):\n{actual.stdout}{actual.stderr}"
        )


def main():
    for source in CASES:
        check(source)
    for source, error in ERRORS:
        check(source, error)
    rng = random.Random(315)
    expressions = []
    for _ in range(300):
        a, b = rng.randint(-100000, 100000), rng.choice([x for x in range(-31, 32) if x])
        op = rng.choice(["+", "-", "*", "//", "%", "&", "|", "^", "<", "<=", ">", ">=", "==", "!="])
        expressions.append(f"print(({a}) {op} ({b}))")
    check("\n".join(expressions))
    floats = []
    while len(floats) < 300:
        value = struct.unpack("d", rng.getrandbits(64).to_bytes(8, sys.byteorder))[0]
        if math.isfinite(value):
            floats.append(f"print({value!r})")
    check("\n".join(floats))
    with tempfile.TemporaryDirectory() as temp:
        Path(temp, "helper.py").write_text("print('loaded')\nx = 40\ndef add(y):\n    return x + y\n")
        source = "import helper\nimport helper as h\nfrom helper import add as f\nprint(helper.x, h is helper, f(2))"
        expected = run([sys.executable], source, temp)
        actual = run([ENGINE], source, temp)
        assert expected.returncode == actual.returncode == 0
        assert expected.stdout == actual.stdout, (expected, actual)
    print(f"Differential: {len(CASES)} programs, {len(ERRORS)} errors, 300 integer expressions, 300 floats, imports passed")


if __name__ == "__main__":
    main()
