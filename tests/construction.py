"""Construction matrix supplementing CPython test_descr and test_raise.

Checks the object.__new__/__init__ argument rules from test_object_new,
with ordinary calls and direct allocator/initializer calls kept distinct.
The unchanged upstream modules still require unimplemented prerequisites.
"""

from pathlib import Path
import subprocess
import sys


ALLOCATORS = [
    'pass',
    '__new__ = object.__new__',
    'def __new__(cls, *args, **kw): return object.__new__(cls)',
    '@staticmethod\n    def __new__(cls, *args, **kw): return object.__new__(cls)',
    '@classmethod\n    def __new__(owner, cls, *args, **kw): return object.__new__(cls)',
    'def __new__(cls, *args, **kw): return 42',
]
INITIALIZERS = [
    'pass',
    '__init__ = object.__init__',
    'def __init__(self, *args, **kw): self.seen = args, kw',
    'def __init__(self, *args, **kw): return 1',
]


def main():
    engine = str(Path(sys.argv[1]).resolve())
    for allocator in ALLOCATORS:
        for initializer in INITIALIZERS:
            source = f'class C:\n    {allocator}\n    {initializer}\n'
            source += '''
for args, kw in [((), {}), ((1,), {}), ((), {'x': 2}), ((1,), {'x': 2})]:
    for action in ['call', 'allocate', 'initialize']:
        try:
            if action == 'call':
                value = C(*args, **kw)
                print(type(value).__name__, getattr(value, 'seen', None))
            elif action == 'allocate':
                value = object.__new__(C, *args, **kw)
                print(type(value).__name__, getattr(value, 'seen', None))
            else:
                value = object.__new__(C)
                print(object.__init__(value, *args, **kw))
        except Exception as error: print(type(error).__name__)
'''
            expected = subprocess.run([sys.executable, '-I', '-c', source], capture_output=True, text=True, timeout=10)
            actual = subprocess.run([engine, '-c', source], capture_output=True, text=True, timeout=10)
            if expected.returncode or actual.returncode or expected.stdout != actual.stdout:
                raise AssertionError(f'{source}\nCPython:\n{expected.stdout}{expected.stderr}\nspy:\n{actual.stdout}{actual.stderr}')
    print(f'Construction: {len(ALLOCATORS) * len(INITIALIZERS) * 12} allocator and initializer checks passed')


if __name__ == '__main__':
    main()
