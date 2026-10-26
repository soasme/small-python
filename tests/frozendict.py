"""Frozen mapping checks against the pinned Python 3.15 oracle.

Eleven unchanged methods from test_dict and test_builtin run with the test-only
unittest adapter. Pickling, CPython-only decorators, and the full module's
fixtures remain obligations in cpython.py; this is not a whole-module port.
"""

import ast
import doctest
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
    source = (root / 'tests/upstream/cpython/Lib/test/test_dict.py').read_text()
    cls = next(node for node in ast.parse(source).body if isinstance(node, ast.ClassDef) and node.name == 'FrozenDictTests')
    names = ['test_constructor', 'test_copy', 'test_merge', 'test_update',
             'test_items_xor', 'test_repr', 'test_hash', 'test_fromkeys']
    methods = {node.name: node for node in cls.body if isinstance(node, ast.FunctionDef)}
    program = 'import unittest\nclass FrozenDict(frozendict): pass\nclass FrozenDictTests(unittest.TestCase):\n'
    for name in names:
        method = methods[name]
        assert not method.decorator_list, name
        program += ''.join(source.splitlines(keepends=True)[method.lineno - 1:method.end_lineno]) + '\n'
    examples = [doctest.Example(f'FrozenDictTests().{name}()\n', '') for name in names]
    source = (root / 'tests/upstream/cpython/Lib/test/test_builtin.py').read_text()
    classes = {node.name: node for node in ast.parse(source).body if isinstance(node, ast.ClassDef)}
    for class_name, selected in [('BuiltinTest', ['test_eval_frozendict', 'test_exec_frozendict']),
                                 ('TestType', ['test_type_frozendict'])]:
        program += f'class {class_name}(unittest.TestCase):\n'
        methods = {node.name: node for node in classes[class_name].body if isinstance(node, ast.FunctionDef)}
        for name in selected:
            method = methods[name]
            assert not method.decorator_list, name
            program += ''.join(source.splitlines(keepends=True)[method.lineno - 1:method.end_lineno]) + '\n'
            examples.append(doctest.Example(f'{class_name}().{name}()\n', ''))
            names.append(name)
    oracle = subprocess.run([sys.executable, '-I', '-c', program + ''.join(e.source for e in examples)], capture_output=True, text=True, timeout=30)
    assert oracle.returncode == 0, oracle.stderr
    replies, error = run_group(root / 'run-cython', program, examples, 30, root / 'tests/support')
    assert not error and replies[0]['ok'], (error, replies)
    failures = [(name, reply) for name, reply in zip(names, replies[1:]) if not reply['ok']]
    assert not failures, failures
    check(engine, '''
        class F(frozendict): pass
        for cls in [dict, frozendict, F]:
            d = cls(a=1, b=2, c=3)
            print(type(d).__name__, repr(d), len(d), bool(d), bool(cls()), d == dict(d))
            print(list(d), list(reversed(d)), list(d.keys()), list(d.values()), list(d.items()))
            print(list(reversed(d.keys())), list(reversed(d.values())), list(reversed(d.items())))
            print(type(d.keys().mapping).__name__, d.keys().mapping == d)
            if cls is not dict:
                print(d.__getnewargs__(), frozendict.__getnewargs__(d))
            print(d['a'], d.get('no'), d.get('no', 9), 'a' in d, 'no' in d)
            print({**d})
            def f(**kw): return kw
            print(f(**d))
            match d:
                case {'a': x, **rest}: print('match', x, rest)
            match d:
                case frozendict(x): print('self', x is d)
            for other in [dict(b=5), frozendict(b=5), F(b=5)]:
                print(type(d | other).__name__, d | other, type(other | d).__name__, other | d)
        class Missing(frozendict):
            def __missing__(self, key): return ('missing', key)
        d = Missing()
        print(d[7], frozendict.__getitem__(d, 7), d.get(7))
        d = frozendict(a=[])
        d['a'].append(d)
        print(d)
        print(frozendict[str, int])
        print(issubclass(frozendict, dict), isinstance(frozendict(), dict))
        d = F(a=1)
        exact = frozendict(a=1)
        print(d.copy() is d.copy(), frozendict.copy(d) is frozendict.copy(d))
        print(F() | exact is exact, frozendict.__or__(F(), exact) is exact)
        print(frozendict.__hash__(d) == hash(d), d.__hash__() == hash(d))
        class Hidden(F):
            def keys(self): print('keys'); return ['b']
            def __getitem__(self, key): print('get', key); return 4
        class Iterated(Hidden):
            def __iter__(self): return iter(['b'])
        for cls in [Hidden, Iterated]:
            print(frozendict() | cls(a=1))
        for name in ['update', 'clear', 'pop', 'popitem', 'setdefault', '__setitem__', '__delitem__', '__ior__']:
            print(name, hasattr(frozendict(), name), hasattr(frozendict, name))
    ''')
    check(engine, '''
        calls = []
        class Key:
            def __repr__(self): return 'Key()'
            def __hash__(self):
                calls.append('key')
                return 17
        class Value:
            def __hash__(self):
                calls.append('value')
                return 29
        key, value = Key(), Value()
        source = {key: value}
        d = frozendict(source)
        print(calls)
        print(hash(d) == hash(d), calls)
        print(hash(d) == hash(frozenset(d.items())))
        print(dict(d) == source, frozendict(d) is d)
        d2 = frozendict(d, x=1)
        print(d2 == {**source, 'x': 1}, d == source)
        print(d.copy() is d)
        print(dict.fromkeys(d), frozendict.fromkeys(d))
        print(calls)
        for d in [frozendict(), frozendict(a=1)]:
            print(hash(d) == hash(frozenset(d.items())))
    ''')
    check(engine, '''
        class HashError:
            def __hash__(self): raise KeyError('error')
        class HashTypeError:
            def __hash__(self): raise TypeError('hash failure')
        class DerivedError(TypeError): pass
        class HashDerivedError:
            def __hash__(self): raise DerivedError('preserved')
        d = frozendict(a=1)
        print(frozendict.__new__(frozendict, d) is d)
        for key in [[], HashError(), HashTypeError(), HashDerivedError()]:
            for op in [lambda: key in d, lambda: d[key], lambda: d.get(key), lambda: frozendict([(key, 1)])]:
                try: op()
                except BaseException as error: print(type(error).__name__, str(error))
        for source in ["d['a'] = 2", "del d['a']", "dict.__init__(d, b=3)",
                       "dict.__setitem__(d, 'a', 2)", "dict.update(d, b=3)"]:
            try: exec(source)
            except TypeError: print('immutable', d)
        for source in ['x', 'data.append(x)', 'x = 2', 'del x', 'global x\\nx = 2', 'global x\\ndel x']:
            for builtins in [False, True]:
                ns = frozendict(x=1, data=[], **({'__builtins__': {}} if builtins else {}))
                try:
                    if source == 'x': print(eval(source, ns))
                    else: exec(source, ns)
                except BaseException as error: print(type(error).__name__, str(error))
                print(ns['x'], ns['data'])
        ns = frozendict(x=3, __builtins__=frozendict(answer=lambda: 4))
        local = {}
        exec('def read(): return x + answer()', ns, local)
        print(local['read'](), local['read'].__globals__ is ns)
        print(type('A', (), frozendict(x=4)).x)
        for op in [eval, exec]:
            try: op('', frozendict())
            except BaseException as error: print(type(error).__name__, str(error))
    ''')
    print('Frozen dictionaries: 11 unchanged upstream methods, mapping protocols, subclasses, hashing and mutation checks passed')


if __name__ == '__main__':
    main()
