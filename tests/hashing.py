"""Hash and dictionary checks supplementing CPython test_hash and test_dict.

String and identity hashes are implementation-specific. Compare their equality
contracts, not process-specific CPython hash values. Tuple hash caching is new
in CPython 3.15 and is checked only with that oracle.
"""

from pathlib import Path
import random
import struct
import subprocess
import sys
import textwrap


def check(engine, source):
    expected = subprocess.run([sys.executable, '-I', '-c', source], capture_output=True, text=True, timeout=15)
    actual = subprocess.run([engine, '-c', source], capture_output=True, text=True, timeout=15)
    if expected.returncode or actual.returncode or expected.stdout != actual.stdout:
        raise AssertionError(f'{source}\nCPython:\n{expected.stdout}{expected.stderr}\nspy:\n{actual.stdout}{actual.stderr}')


def main():
    engine = str(Path(sys.argv[1]).resolve())
    rng = random.Random(315)
    values = ['0', '1', '-1', '-2', 'True', 'False', '()', '(1, 2, 3)', 'slice(1, 2, 3)',
              'range(1, 9, 2)', 'complex(0, -1)', "float('inf')", "float('-inf')"]
    for _ in range(300):
        integer = rng.getrandbits(rng.randrange(1, 2000)) * rng.choice([-1, 1])
        values.append(repr(integer))
        number = struct.unpack('d', rng.randbytes(8))[0]
        if number == number and abs(number) != float('inf'):
            values += [repr(number), f'complex({number!r}, {rng.randrange(-100, 101)})']
    for start in range(0, len(values), 100):
        check(engine, '\n'.join(f'print(hash({value}))' for value in values[start:start + 100]))
    protocols = '''
    class Hashed:
        def __init__(self, value):
            self.value = value
            self.hash_count = self.eq_count = 0
            self.fail = False
        def __hash__(self):
            self.hash_count += 1
            if self.fail: raise ValueError('hash')
            return 42
        def __eq__(self, other):
            self.eq_count += 1
            return self is other
    first, second = Hashed(1), Hashed(2)
    d = {first: 5}
    d.setdefault(second, []).append(3)
    print(first.hash_count, second.hash_count, first.eq_count + second.eq_count)
    copied = d.copy()
    print(first.hash_count, second.hash_count, copied == d, copied is d)
    first.fail = True
    for action in ['get', 'pop', 'setdefault', 'item', 'contains', 'assign', 'delete']:
        try:
            if action == 'item': d[first]
            elif action == 'contains': first in d
            elif action == 'assign': d[first] = 4
            elif action == 'delete': del d[first]
            else: getattr(d, action)(first)
        except ValueError as error: print(action, error)
    print(d.copy() == d)
    merged = dict(d)
    merged.update(d)
    print(merged == d)
    first.fail = False
    print(d.pop(second), len(d), d.pop(first), len(d))
    print(d.setdefault('a'), d.setdefault('a', 42), d.setdefault('b', 43))
    print(d.popitem(), d.popitem(), d.pop('missing', 'fallback'))
    try: d.popitem()
    except KeyError: print('empty popitem')
    d['cycle'] = d
    copied = d.copy()
    print(copied['cycle'] is d, d.clear(), copied['cycle'])
    for action in ['item', 'pop', 'delete']:
        key = ('missing', 42)
        try:
            if action == 'item': d[key]
            elif action == 'delete': del d[key]
            else: d.pop(key)
        except KeyError as error: print(error.args[0] is key, error.args)
    for value in [[], {}, set(), ([],), slice([], 1), slice(1, [])]:
        try: hash(value)
        except TypeError: print('unhashable')
    class Custom:
        def __hash__(self): return result
    for result in [-1, -(2**63), 2**63 - 1, 2**1000, -(2**1000), 1.5, 'bad']:
        try: print(hash(Custom()))
        except TypeError: print('invalid hash result')
    class Default: pass
    value = Default()
    print(hash(value) == object.__hash__(value))
    class Equality:
        def __eq__(self, other): return True
    try: hash(Equality())
    except TypeError: print('equality disables inherited hash')
    class Restore(Equality): __hash__ = object.__hash__
    print(isinstance(hash(Restore()), int))
    d = {1: 'int', 1.0: 'float', 1+0j: 'complex', True: 'bool'}
    print(len(d), d[1], d[1.0], d[1+0j], d[True])
    nan = float('nan')
    d = {nan: 42}
    print(d[nan], nan in d, hash(nan) == hash(nan))
    print(hash('abc') == hash('a' + 'bc'), hash(b'abc') == hash(b'a' + b'bc'))
    for value in [0, True, 1.25, 1+2j, 'hello', b'hello', (1, 2), slice(1, 2), range(3)]:
        print(hash(value) == value.__hash__(), hash(value) == type(value).__hash__(value))
    print(list.__hash__, dict.__hash__, set.__hash__)
    try: int.__hash__('wrong type')
    except TypeError: print('hash descriptor type check')
    for left, right in [(range(0), range(1, 1)), (range(1, 2), range(1, 9, 10)),
                        (range(0, 6, 2), range(0, 5, 2))]:
        print(left == right, hash(left) == hash(right))
    '''
    check(engine, textwrap.dedent(protocols))
    check(engine, textwrap.dedent('''
    class Collision:
        def __hash__(self): return 7
        def __eq__(self, other):
            d.clear()
            return True
    for action in ['item', 'get', 'pop', 'setdefault', 'contains', 'assign', 'delete']:
        d = {Collision(): 1}
        key = Collision()
        try:
            if action == 'item': print(d[key])
            elif action == 'contains': print(key in d)
            elif action == 'assign': d[key] = 42; print(d[key])
            elif action == 'delete': del d[key]
            else: print(getattr(d, action)(key, 42))
        except KeyError: print('missing')
        print(len(d))
    class Bad:
        def __hash__(self): return 7
        def __eq__(self, other): raise ValueError('compare')
    d = {Bad(): 1}
    for action in ['get', 'pop', 'setdefault']:
        try: getattr(d, action)(Bad())
        except ValueError as error: print(error)
    '''))
    if sys.version_info >= (3, 15):
        check(engine, textwrap.dedent('''
        class Key:
            def __hash__(self):
                print('hash')
                return 1
        key = Key()
        pair = (key,)
        hash(pair)
        hash(pair)
        d = {pair: 1}
        print(d[pair])
        '''))
    print(f'Hashing: {len(values)} numeric/compound hashes and dictionary protocol checks passed')


if __name__ == '__main__':
    main()
