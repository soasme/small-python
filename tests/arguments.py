"""Argument-binding matrix supplementing the unchanged test_extcall doctests."""

from pathlib import Path
import subprocess
import sys
import textwrap


SIGNATURES = [
    ('', '()'),
    ('a', '(a,)'),
    ('a, b, c', '(a, b, c)'),
    ('a=1, b=2', '(a, b)'),
    ('a, /, b=2', '(a, b)'),
    ('a, /, **kw', '(a, kw)'),
    ('*args', 'args'),
    ('*, a, b', '(a, b)'),
    ('a, *args, b=2, **kw', '(a, args, b, kw)'),
    ('a, /, b, *args, c, d=4, **kw', '(a, b, args, c, d, kw)'),
]


def check_protocols(engine):
    source = textwrap.dedent('''
    class Name(str): pass
    a = Name('a')
    def named(a): return a
    def extra(**kw): return kw
    print(named(**{a: 42}))
    kw = extra(**{a: 43})
    print(next(iter(kw)) is a, kw[a])
    print(1, 2, **{Name('sep'): ':'})
    print(sorted([3, 1, 2], **{Name('reverse'): True}))
    print(pow(**{Name('base'): 2, Name('exp'): 3}))
    print(int('10', **{Name('base'): 2}))
    class Alias(str):
        def __eq__(self, other): return other == 'a'
        __hash__ = str.__hash__
    print(named(**{Alias('alias'): 44}))
    class Broken(str):
        def __eq__(self, other): raise ValueError('keyword comparison')
        __hash__ = str.__hash__
    try: named(**{Broken('a'): 1})
    except ValueError as error: print(error)
    class NoIteration: pass
    class Disabled:
        __iter__ = None
    class Raises:
        def __iter__(self): raise TypeError('iterator error')
    for value in [NoIteration(), Disabled(), Raises()]:
        try: extra(*value)
        except TypeError as error: print(type(error).__name__, 'iterator error' in str(error))
    def mapping(): pass
    mapping.keys = lambda: ['a']
    try: named(**mapping)
    except TypeError: print('keys alone do not make an object subscriptable')
    class BrokenKeys:
        def keys(self): raise ValueError('keys error')
    try: named(**BrokenKeys())
    except ValueError as error: print(error)
    ''')
    expected = subprocess.run([sys.executable, '-I', '-c', source], capture_output=True, text=True, timeout=10)
    actual = subprocess.run([engine, '-c', source], capture_output=True, text=True, timeout=10)
    if expected.returncode or actual.returncode or expected.stdout != actual.stdout:
        raise AssertionError(f'{source}\nCPython:\n{expected.stdout}{expected.stderr}\nspy:\n{actual.stdout}{actual.stderr}')


def main():
    engine = str(Path(sys.argv[1]).resolve())
    check_protocols(engine)
    arguments = [tuple(range(count)) for count in range(7)]
    keywords = [{}, {'a': 11}, {'b': 22}, {'a': 11, 'b': 22},
                {'zebra': 99}, {'zebra': 99, 'a': 11}, {'a': 11, 'zebra': 99}, {'c': 33, 'd': 44}]
    for signature, result in SIGNATURES:
        source = f'def f({signature}): return {result}\n'
        source += f'''for args in {arguments!r}:
    for kwargs in {keywords!r}:
        try: print(f(*args, **kwargs))
        except TypeError as error: print(type(error).__name__, str(error))
'''
        expected = subprocess.run([sys.executable, '-I', '-c', source], capture_output=True, text=True, timeout=10)
        actual = subprocess.run([engine, '-c', source], capture_output=True, text=True, timeout=10)
        if expected.returncode or actual.returncode or expected.stdout != actual.stdout:
            wanted, found = expected.stdout.splitlines(), actual.stdout.splitlines()
            for index, (a, b) in enumerate(zip(wanted, found)):
                if a != b:
                    raise AssertionError(f'f({signature}), args={arguments[index // len(keywords)]}, '
                                         f'keywords={keywords[index % len(keywords)]}\nCPython: {a}\nspy: {b}')
            raise AssertionError(f'{source}\nCPython:\n{expected.stdout}{expected.stderr}\nspy:\n{actual.stdout}{actual.stderr}')
    print(f'Arguments: {len(SIGNATURES) * len(arguments) * len(keywords)} binding and diagnostic checks passed')


if __name__ == '__main__':
    main()
