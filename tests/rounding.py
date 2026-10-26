"""Rounding oracle supplementing CPython test_builtin, test_float, test_long."""

from pathlib import Path
import random
import struct
import subprocess
import sys
import textwrap


def check(engine, source):
    expected = subprocess.run([sys.executable, '-I', '-c', source], capture_output=True, text=True, timeout=30)
    actual = subprocess.run([engine, '-c', source], capture_output=True, text=True, timeout=30)
    if expected.returncode or actual.returncode or expected.stdout != actual.stdout:
        raise AssertionError(f'{source}\nCPython:\n{expected.stdout}{expected.stderr}\nspy:\n{actual.stdout}{actual.stderr}')


def main():
    engine = str(Path(sys.argv[1]).resolve())
    rng = random.Random(315)
    values = ['0', '-1', 'True', 'False', '0.0', '-0.0', '2.675', '0.125', '-0.125',
              '5e15-1', '5e15', '5e15+1', '5e15+2', '5e15+3', '1.7976931348623157e308',
              '5e-324', "float('inf')", "float('-inf')", "float('nan')"]
    values += [repr(value / 2) for value in range(-101, 102)]
    for _ in range(180):
        number = struct.unpack('d', rng.randbytes(8))[0]
        if number == number and abs(number) != float('inf'):
            values.append(repr(number))
        values.append(repr(rng.getrandbits(rng.randrange(1, 2000)) * rng.choice([-1, 1])))
    # CPython constructs 10**abs(ndigits) for integers. Bound that oracle work;
    # its float implementation can safely accept arbitrarily large ndigits.
    cases = [(value, digits) for value in values
             for digits in ['', ', None', ', 0', ', 2', ', -2', ', 323', ', -308', ', 10**100',
                            ', -10000' if isinstance(eval(value), int) else ', -10**100']]
    for start in range(0, len(cases), 80):
        source = ''
        for value, digits in cases[start:start + 80]:
            source += f'try:\n    value = round({value}{digits})\n    print(type(value).__name__, repr(value))\n'
            source += 'except Exception as error: print(type(error).__name__)\n'
        check(engine, source)
    check(engine, textwrap.dedent('''
    class Index:
        def __index__(self): print('index'); return 2
    print(round(2.675, Index()), round(100, Index()))
    class Rounded:
        def __round__(self, *args): return args
    sentinel = []
    print(round(Rounded()), round(Rounded(), None), round(Rounded(), sentinel)[0] is sentinel)
    class Missing: pass
    missing = Missing()
    missing.__round__ = lambda: 42
    try: round(missing)
    except TypeError: print('special lookup ignores instance attribute')
    class Broken:
        def __index__(self): raise ValueError('index failure')
    for value in [1, 1.2, float('inf')]:
        try: round(value, Broken())
        except ValueError as error: print(error)
    for value in [1, 1.2, float('nan')]:
        try: round(value, 1.2)
        except TypeError: print('digits must be integer')
    print(round(number=-8.0, ndigits=-1), round(ndigits=2, number=2.675))
    for kwargs in [{'number': 1}, {'unknown': 1}]:
        try: round(1.2, **kwargs)
        except TypeError: print('invalid arguments')
    for value in [True, 1, -135, 1.25, -1.25]:
        print(value.__round__(), value.__round__(1), type(value).__round__(value, 1))
    try: float.__round__(1)
    except TypeError: print('descriptor type check')
    '''))
    print(f'Rounding: {len(cases)} numeric cases and special-method/argument checks passed')


if __name__ == '__main__':
    main()
