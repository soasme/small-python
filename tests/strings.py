"""Differential checks of text, bytes, set, and conversion methods."""

from pathlib import Path
import random
import subprocess
import sys
import textwrap


PROGRAM = """
def show(thunk):
    try:
        print(repr(thunk()))
    except Exception as error:
        print(type(error).__name__)
"""


def literal(rng, alphabet, size):
    return "".join(rng.choice(alphabet) for _ in range(rng.randrange(size)))


def check_bytearray_callbacks(engine):
    # CPython test_bytes.test_mutating_index and test_mutating_index_inbounds
    # exercise these buffer invalidation paths. Its C API variants stay unported.
    source = textwrap.dedent('''
    class Index:
        def __init__(self, array, replacement, value):
            self.array, self.replacement, self.value = array, replacement, value
        def __index__(self):
            self.array.clear()
            self.array.extend(self.replacement)
            return self.value
    for initial in [b'', b'abc', b'abcdef']:
        for replacement in [b'', b'X', b'XYZW']:
            for operation in range(8):
                a = bytearray(initial)
                index = Index(a, replacement, 0)
                value = Index(a, replacement, 88)
                try:
                    if operation == 0: a[0] = value
                    elif operation == 1: a[index] = 89
                    elif operation == 2: a.append(value)
                    elif operation == 3: print('pop', a.pop(index))
                    elif operation == 4: a.insert(index, value)
                    elif operation == 5: a.remove(value)
                    elif operation == 6: del a[index]
                    else: a.extend([value])
                except Exception as error: print(type(error).__name__)
                print(a)
    for step in [1, 2, -1, -2]:
        for replacement in [b'', b'X', b'XYZW']:
            a = bytearray(b'abc')
            start = Index(a, replacement, 0)
            try: del a[start::step]
            except Exception as error: print(type(error).__name__)
            print(a)
            a = bytearray(b'abc')
            start = Index(a, replacement, 0)
            try: a[start::step] = b'XY'
            except Exception as error: print(type(error).__name__)
            print(a)
    a = bytearray(b'abc')
    a[:] = a
    print(a)
    del a[::2]
    print(a)
    for obj in ['', b'', bytearray()]:
        for method in ['center', 'join', 'partition', 'removeprefix', 'translate']:
            try: getattr(obj, method)()
            except TypeError: print('missing argument')
            try: getattr(obj, method)(unexpected=1)
            except TypeError: print('unexpected keyword')
    for method in ['append', 'extend', 'insert', 'remove']:
        try: getattr(bytearray(), method)()
        except TypeError: print('missing bytearray argument')
        try: getattr(bytearray(), method)(unexpected=1)
        except TypeError: print('unexpected bytearray keyword')
    ''')
    expected = subprocess.run([sys.executable, '-I', '-c', source], capture_output=True, text=True, timeout=30)
    actual = subprocess.run([engine, '-c', source], capture_output=True, text=True, timeout=30)
    if expected.returncode or actual.returncode or expected.stdout != actual.stdout:
        raise AssertionError(f'{source}\nCPython:\n{expected.stdout}{expected.stderr}\nspy:\n{actual.stdout}{actual.stderr}')


def check_bytearray_take_bytes(engine):
    # Operations from upstream test_bytes.test_take_bytes and its reentrant
    # resize regression. Buffer-export and CPython allocation tests remain gaps.
    source = textwrap.dedent('''
    def take(target, replacement, n):
        class Evil:
            def __index__(self):
                target.clear()
                target.extend(replacement)
                return n
        return target.take_bytes(Evil())
    for initial in [b'', b'a', b'abcdefgh']:
        for replacement in [b'', b'xy', b'abcdefghij']:
            for n in [-12, -3, -1, 0, 1, 3, 8, 11]:
                a = bytearray(initial)
                try: print(take(a, replacement, n))
                except Exception as error: print(type(error).__name__)
                print(a)
    for n in [None, 0, 1, -1, 10**100, -10**100, 3.14, 'x']:
        a = bytearray(b'abc')
        try: print(a.take_bytes(n))
        except Exception as error: print(type(error).__name__)
        print(a)
    class Array(bytearray): pass
    for cls in [bytearray, Array]:
        a = cls(b'abcdef')
        print(a.take_bytes(2), a.take_bytes(-1), a.take_bytes(), bytes(a))
        for n in [10, 3, 0, 7, -1, 3.5]:
            try: print(a.resize(n))
            except Exception as error: print(type(error).__name__)
            print(bytes(a))
    for step in [-3, -1, 1, 2, 3]:
        a = bytearray(b'abcdefgh')
        a[::step] = b''
        print(a)
    ''')
    expected = subprocess.run([sys.executable, '-I', '-c', source], capture_output=True, text=True, timeout=30)
    actual = subprocess.run([engine, '-c', source], capture_output=True, text=True, timeout=30)
    if expected.returncode or actual.returncode or expected.stdout != actual.stdout:
        raise AssertionError(f'{source}\nCPython:\n{expected.stdout}{expected.stderr}\nspy:\n{actual.stdout}{actual.stderr}')


def main():
    engine = str(Path(sys.argv[1]).resolve())
    check_bytearray_callbacks(engine)
    if sys.version_info >= (3, 15):
        check_bytearray_take_bytes(engine)
    rng = random.Random(3150)
    text_alphabet = "ab AB,.-\t\n_1ßΣσİǆé"
    expressions = []
    methods = ["lower()", "upper()", "casefold()", "title()", "capitalize()", "swapcase()", "isalpha()",
               "isdecimal()", "isdigit()", "isnumeric()", "isspace()", "isalnum()", "isascii()", "isupper()",
               "islower()", "istitle()", "split()", "rsplit()", "strip()", "lstrip()", "rstrip()",
               "expandtabs()", "expandtabs(3)", "encode()", "encode('ascii', 'replace')",
               "encode('latin-1', 'xmlcharrefreplace')", "encode('ascii', 'backslashreplace')", "zfill(9)"]
    for _ in range(400):
        text = repr(literal(rng, text_alphabet, 12))
        method = rng.choice(methods)
        expressions.append(f"{text}.{method}")
        sep = repr(literal(rng, "ab ,", 3))
        count = rng.randrange(-1, 4)
        expressions.append(f"{text}.split({sep}, {count})")
        expressions.append(f"{text}.rsplit({sep}, maxsplit={count})")
        expressions.append(f"{text}.replace({sep}, 'XY', {count})")
        expressions.append(f"{text}.partition({sep}), {text}.rpartition({sep})")
        expressions.append(f"{text}.strip({sep}), {text}.removeprefix({sep}), {text}.removesuffix({sep})")
        width = rng.randrange(0, 20)
        expressions.append(f"{text}.center({width}, '*'), {text}.ljust({width}), {text}.rjust({width}, '-')")
    byte_alphabet = "ab AB,.\t\n19"
    for _ in range(200):
        data = "b" + repr(literal(rng, byte_alphabet, 10))
        method = rng.choice(["lower()", "upper()", "title()", "swapcase()", "capitalize()", "isalpha()",
                             "isspace()", "split()", "strip()", "hex()", "hex(':', 2)", "decode()", "zfill(6)"])
        expressions.append(f"{data}.{method}")
        expressions.append(f"bytearray({data}).{method}")
        sep = "b" + repr(literal(rng, "a ,", 3))
        expressions.append(f"{data}.split({sep}), {data}.replace({sep}, b'-'), {data}.partition({sep})")
    for _ in range(200):
        a = {rng.randrange(8) for _ in range(rng.randrange(6))}
        b = {rng.randrange(8) for _ in range(rng.randrange(6))}
        expressions.append(f"sorted(set({sorted(a)}) | set({sorted(b)})), sorted(set({sorted(a)}) & set({sorted(b)}))")
        expressions.append(f"sorted(set({sorted(a)}) - set({sorted(b)})), sorted(set({sorted(a)}) ^ set({sorted(b)}))")
        expressions.append(f"set({sorted(a)}) <= set({sorted(b)}), set({sorted(a)}) < set({sorted(b)}), "
                           f"set({sorted(a)}).isdisjoint({sorted(b)}), frozenset({sorted(a)}) == set({sorted(a)})")
        expressions.append(f"hash(frozenset({sorted(a)})) == hash(frozenset({sorted(a)[::-1]}))")
    for _ in range(200):
        value = rng.getrandbits(rng.randrange(1, 80)) * rng.choice((-1, 1))
        length = rng.randrange(0, 12)
        order = rng.choice(("'big'", "'little'"))
        expressions.append(f"({value}).to_bytes({length}, {order}, signed=True)")
        expressions.append(f"int.from_bytes(({value}).to_bytes(12, {order}, signed=True), {order}, signed=True)")
        expressions.append(f"int.from_bytes(bytes({[rng.randrange(256) for _ in range(length)]}), {order})")
    for _ in range(100):
        x = rng.choice([rng.uniform(-1e6, 1e6), rng.random(), float(rng.randrange(-100, 100)), 1e300, 5e-324])
        expressions.append(f"({x!r}).as_integer_ratio(), ({x!r}).is_integer(), ({x!r}).hex(), float.fromhex(({x!r}).hex())")
    expressions.extend([
        "'\\udc80'.encode()", "'\\udc80'.encode('utf-8', 'surrogatepass')", "b'\\xff'.decode()",
        "b'\\xff'.decode('utf-8', 'replace')", "b'\\xff\\xfe'.decode('ascii', 'backslashreplace')",
        "b'\\xed\\xa0\\x80'.decode('utf-8', 'surrogatepass')", "b'\\xe2\\x82'.decode('utf-8', 'ignore')",
        "'abc'.translate(str.maketrans('ab', 'xy', 'c'))", "'abc'.translate({97: None, 98: 'zz'})",
        "b'abc'.translate(None, b'b')", "'{a}-{b}'.format_map({'a': 1, 'b': 2})", "str(b'ab', 'ascii')",
        "bytes('é', 'utf-8')", "bytearray('x', 'ascii')", "bytes.fromhex('de ad be ef')",
        "bytearray.fromhex('00ff')", "dict.fromkeys('ab', 0)", "list(filter(lambda x: x % 2, range(7)))",
        "max([], default=3)", "min('bca', key=ord)", "max(1, 2, 3, key=lambda x: -x)", "sum([[1], [2]], start=[])",
        "'a'.center(4, 'xy')", "'x'.zfill(-1)", "''.split(',')", "'a,b'.split('')",
        "frozenset([1, 2]) | {3}", "{1} | frozenset([2])", "repr(frozenset())", "{frozenset([1]): 1}[frozenset([1])]",
        "{1, 2}.issubset([1, 2, 3])", "set([1]).union([2], (3,))", "set([1, 2]).intersection([2], [2, 3])",
        "bytearray(b'abc') + b'd'", "b'd' + bytearray(b'abc')", "bytearray(3)", "len(bytearray(b'ab'))",
        "b'ab' == bytearray(b'ab')", "bytearray(b'a') < b'b'", "b'a' in bytearray(b'cab')", "98 in bytearray(b'b')",
    ])
    source = PROGRAM + "".join(f"show(lambda: ({expression}))\n" for expression in expressions)
    expected = subprocess.run([sys.executable, "-c", source], capture_output=True, text=True, timeout=60)
    if expected.returncode:
        raise AssertionError(expected.stderr)
    actual = subprocess.run([engine, "-c", source], capture_output=True, text=True, timeout=60)
    if actual.returncode:
        raise AssertionError(actual.stderr)
    for expression, want, got in zip(expressions, expected.stdout.splitlines(), actual.stdout.splitlines()):
        if want != got:
            raise AssertionError(f"{expression}: {got} != {want}")
    if len(actual.stdout.splitlines()) != len(expressions):
        raise AssertionError("missing output")
    print(f"Strings: {len(expressions)} text/bytes/set/conversion expressions plus bytearray callback and argument checks passed")


if __name__ == "__main__":
    main()
