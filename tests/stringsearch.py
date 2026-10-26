"""String search checks from pinned string_tests.py and a differential matrix.

Literal checkequal calls are supplementary example coverage, not passing whole
upstream test methods. Their loops, fixtures, and nonliteral calls remain in the
full-module port obligation recorded by cpython.py.
"""

import ast
from pathlib import Path
import random
import subprocess
import sys


METHODS = ('startswith', 'endswith', 'find', 'rfind', 'index', 'rindex', 'count')


def run(engine, source):
    result = subprocess.run([engine, '-c', source], capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise AssertionError(f'{source}\n{result.stdout}{result.stderr}')
    return result.stdout


def main():
    engine = str(Path(sys.argv[1]).resolve())
    path = Path(__file__).parent / 'upstream/cpython/Lib/test/string_tests.py'
    upstream = ast.parse(path.read_text())
    examples = []
    for definition in ast.walk(upstream):
        if not isinstance(definition, ast.FunctionDef) or definition.name not in {'test_' + method for method in METHODS}:
            continue
        for call in ast.walk(definition):
            if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute) or call.func.attr != 'checkequal':
                continue
            try:
                expected, text, method, *args = [ast.literal_eval(arg) for arg in call.args]
            except (ValueError, TypeError):
                continue
            if method in METHODS:
                for binary in (False, True):
                    # Integer needles are in upstream's contains_bytes branch.
                    # Unicode examples retain their original character indices.
                    if not binary and args and isinstance(args[0], int): continue
                    def convert(value):
                        if isinstance(value, tuple): return tuple(convert(part) for part in value)
                        return value.encode('ascii') if binary and isinstance(value, str) else value
                    try:
                        expression = f'{convert(text)!r}.{method}({", ".join(repr(convert(arg)) for arg in args)})'
                    except UnicodeEncodeError:
                        continue
                    examples.append((expression, expected, call.lineno))
    if not examples:
        raise AssertionError('missing pinned upstream string-search examples')
    for start in range(0, len(examples), 80):
        batch = examples[start:start + 80]
        source = ''.join(f'print({expression})\n' for expression, _, _ in batch)
        expected = ''.join(f'{value}\n' for _, value, _ in batch)
        for interpreter in [sys.executable, engine]:
            actual = run(interpreter, source)
            if actual != expected:
                raise AssertionError(f'{path} source lines {[line for _, _, line in batch]}\n{source}\nexpected:\n{expected}\nactual:\n{actual}')
    rng = random.Random(315)
    cases = []
    for i in range(800):
        text = ''.join(rng.choices('abcé中\0\ud800', k=rng.randrange(40)))
        needle = ''.join(rng.choices('abcé中\0\ud800', k=rng.randrange(8)))
        if i % 3 == 0: needle = text[rng.randrange(len(text) + 1):]
        if i % 2 == 0:
            text, needle = text.encode('utf-8', 'surrogatepass'), needle.encode('utf-8', 'surrogatepass')
        bounds = rng.choice(['', ', None', ', 0', ', -100, 100', ', 1, 1', ', 10000', ', -10**100, 10**100', ', -3, -1'])
        for method in METHODS:
            cases.append(f'{text!r}.{method}({needle!r}{bounds})')
    for start in range(0, len(cases), 80):
        source = ''.join(f'try: print({expr})\nexcept Exception as error: print(type(error).__name__)\n' for expr in cases[start:start + 80])
        expected = run(sys.executable, source)
        actual = run(engine, source)
        if expected != actual: raise AssertionError(f'{source}\nCPython:\n{expected}\nspy:\n{actual}')
    source = '''
class Bound:
    def __index__(self): print('index'); return 1
print('hello'.startswith(('e', 42), Bound()))
print('hello'.endswith(('o', 42)))
for parts in [(42, 'h'), ('x', 42), ()]:
    try: print('hello'.startswith(parts))
    except TypeError: print('invalid tuple item')
print(b'abcabc'.find(97), b'abcabc'.rfind(97), b'abcabc'.count(97))
class Byte:
    def __index__(self): return 97
print(b'abcabc'.find(Byte()))
print(str.find('abc', 'b'), bytes.count(b'abca', 97))
for value in [-1, 256, 10**100, -10**100]:
    try: b'abc'.find(value)
    except ValueError: print('invalid byte')
text = 'a' * 10000 + 'b'
print(text.find('a' * 1000 + 'b'), text.rfind('a' * 1000 + 'b'))
'''
    expected = run(sys.executable, source)
    actual = run(engine, source)
    if expected != actual: raise AssertionError(f'{source}\nCPython:\n{expected}\nspy:\n{actual}')
    print(f'String search: {len(examples)} upstream literal examples and {len(cases)} differential cases passed')


if __name__ == '__main__':
    main()
