"""Suspension metadata checks, including an unchanged upstream test method.

GeneratorTest.test_name is transplanted with its original class name and body;
only unittest is replaced on spy. This is a selected-method check, not a pass
for test_generators.py. Full module accounting remains in cpython.py.
"""

import ast
from pathlib import Path
import subprocess
import sys
import textwrap

from cpython import verify
from run_cython import run_group


def check(engine, source):
    source = textwrap.dedent(source)
    expected = subprocess.run([sys.executable, '-I', '-c', source], capture_output=True, text=True, timeout=30)
    actual = subprocess.run([engine, '-c', source], capture_output=True, text=True, timeout=30)
    if expected.returncode or actual.returncode or expected.stdout != actual.stdout:
        raise AssertionError(f'{source}\nCPython:\n{expected.stdout}{expected.stderr}\nspy:\n{actual.stdout}{actual.stderr}')


def main():
    root = Path(__file__).resolve().parent.parent
    sys.path[:] = [entry for entry in sys.path if Path(entry).resolve() != root / 'tests']
    verify()
    engine = str(Path(sys.argv[1]).resolve())
    source = (root / 'tests/upstream/cpython/Lib/test/test_generators.py').read_text()
    cls = next(node for node in ast.parse(source).body if isinstance(node, ast.ClassDef) and node.name == 'GeneratorTest')
    method = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == 'test_name')
    body = ''.join(source.splitlines(keepends=True)[method.lineno - 1:method.end_lineno])
    program = 'import unittest\nclass GeneratorTest(unittest.TestCase):\n' + body + '\nGeneratorTest().test_name()\n'
    oracle = subprocess.run([sys.executable, '-I', '-c', program], capture_output=True, text=True, timeout=30)
    assert oracle.returncode == 0, oracle.stderr
    replies, error = run_group(root / 'run-cython', program, [], 30, root / 'tests/support')
    assert not error and replies[0]['ok'], (error, replies)
    check(engine, '''
        class Name(str): pass
        def factory():
            def gen(): yield 1
            async def coro(): return 2
            async def agen(): yield 3
            return gen, coro, agen
        for make in factory():
            old = make()
            make.__name__ = 'renamed'
            make.__qualname__ = 'qualified.renamed'
            new = make()
            print(old.__name__, old.__qualname__, new.__name__, new.__qualname__)
            print(repr(old).split(' at ')[0], repr(new).split(' at ')[0])
            for field in ['__name__', '__qualname__']:
                text = Name('changed')
                setattr(new, field, text)
                print(field, getattr(new, field) is text)
                for value in [None, 17, [], object()]:
                    try: setattr(new, field, value)
                    except TypeError as error: print(str(error))
                try: delattr(new, field)
                except TypeError as error: print(str(error))
            if hasattr(new, 'close'):
                old.close()
                new.close()
            print(new.__name__, new.__qualname__)
    ''')
    check(engine, '''
        def show(g, prefix):
            print(getattr(g, prefix + '_state'), getattr(g, prefix + '_running'), getattr(g, prefix + '_suspended'))
        def gen():
            show(g, 'gi')
            yield 1
            show(g, 'gi')
        g = gen()
        show(g, 'gi')
        next(g)
        show(g, 'gi')
        next(g, None)
        show(g, 'gi')
        class Pause:
            def __await__(self):
                yield 'pause'
        async def coro():
            show(c, 'cr')
            await Pause()
            show(c, 'cr')
        c = coro()
        show(c, 'cr')
        c.send(None)
        show(c, 'cr')
        try: c.send(None)
        except StopIteration: pass
        show(c, 'cr')
        async def agen():
            show(a, 'ag')
            yield 1
            await Pause()
            show(a, 'ag')
        a = agen()
        show(a, 'ag')
        for i in range(3):
            op = a.__anext__()
            try: print(op.send(None))
            except (StopIteration, StopAsyncIteration): pass
            show(a, 'ag')
            if a.ag_running:
                try: op.send(None)
                except StopAsyncIteration: pass
                show(a, 'ag')
    ''')
    print('Suspension metadata: unchanged GeneratorTest.test_name, names, reprs and lifecycle states passed')


if __name__ == '__main__':
    main()
