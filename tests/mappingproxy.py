"""Mapping-proxy checks informed by CPython test_types.MappingProxyTests.

These differential checks supplement the unchanged whole-module ledger; they
do not count as a passing test_types module.
"""

from pathlib import Path
import subprocess
import sys
import textwrap


def check(engine, source):
    source = 'from types import MappingProxyType as Proxy\n' + textwrap.dedent(source)
    expected = subprocess.run([sys.executable, '-I', '-c', source], capture_output=True, text=True, timeout=30)
    actual = subprocess.run([engine, '-c', source], capture_output=True, text=True, timeout=30)
    if expected.returncode or actual.returncode or expected.stdout != actual.stdout:
        raise AssertionError(f'{source}\nCPython:\n{expected.stdout}{expected.stderr}\nspy:\n{actual.stdout}{actual.stderr}')


def main():
    engine = str(Path(sys.argv[1]).resolve())
    check(engine, '''
        mapping = {'a': 1, 'b': 2}
        proxy = Proxy(mapping=mapping)
        print(str(proxy), repr(proxy), proxy.__repr__(), proxy.__str__())
        print(len(proxy), bool(proxy), list(proxy), list(reversed(proxy)))
        print(proxy['a'], proxy.get('a'), proxy.get('missing'), proxy.get('missing', 42))
        print('a' in proxy, 'missing' not in proxy, dict(proxy), proxy.copy())
        views = proxy.keys(), proxy.values(), proxy.items()
        mapping['c'] = 3
        print([list(view) for view in views], proxy['c'])
        mapping.clear()
        print(len(proxy), bool(proxy), list(proxy))
        for kind in ['keys', 'values', 'items']:
            d = {'a': 1}
            view = getattr(d, kind)()
            p = view.mapping
            print(type(p) is Proxy, p == d, p is view.mapping)
            d['b'] = 2
            print(dict(p))
        print(Proxy.__new__(Proxy, {'a': 1}))
        print(Proxy[str, int], Proxy[str, int].__origin__ is Proxy)
        for mapping in [42, [], (), bytearray(b'a'), 'abc', range(3)]:
            try:
                result = Proxy(mapping)
                print(type(mapping).__name__, len(result), result[0])
            except TypeError: print(type(mapping).__name__, 'type error')
        try:
            class Sub(Proxy): pass
        except TypeError: print('final')
        for source in ['Proxy()', 'Proxy({}, {})', 'Proxy(unknown={})',
                       'proxy[1] = 2', 'del proxy[1]', 'proxy.extra = 1',
                       'proxy._mapping', 'proxy.get(key=1)', 'proxy.copy(1)']:
            try: exec(source)
            except (TypeError, AttributeError): print('rejected', source)
            else: raise AssertionError(source)
    ''')
    check(engine, '''
        events = []
        class Custom(dict):
            def __contains__(self, key):
                events.append(('contains', key))
                return key == 'magic' or dict.__contains__(self, key)
            def __iter__(self): return iter(('iter',))
            def __reversed__(self): return iter(('reverse',))
            def __len__(self): return 500
            def __bool__(self): return False
            def copy(self): return 'copy'
            def keys(self): return 'keys'
            def items(self): return 'items'
            def values(self): return 'values'
            def __getitem__(self, key): return 'getitem=%s' % dict.__getitem__(self, key)
            def __missing__(self, key): return 'missing=%s' % key
            def get(self, key, default=None):
                events.append(('get', key, default))
                return dict.get(self, key, default)
            def __hash__(self): return 3844817361
        mapping = Custom({'key': 'value'})
        proxy = Proxy(mapping)
        print('key' in proxy, 'magic' in proxy, 'xxx' in proxy)
        print(proxy['key'], proxy['missing'], proxy.get('key'), proxy.get('xxx'), proxy.get('xxx', 42))
        print(tuple(proxy), tuple(reversed(proxy)), len(proxy), bool(proxy), bool(mapping))
        print(proxy.copy(), proxy.keys(), proxy.items(), proxy.values(), hash(proxy), events)
        class Mapping:
            def __getitem__(self, key): return key * 2
            def __len__(self): return 0
            def get(self, *args): return args
        proxy = Proxy(Mapping())
        print(proxy[3], proxy.get(3), proxy.get(3, 4), bool(proxy))
        try: proxy.keys()
        except AttributeError: print('missing mapping method')
    ''')
    check(engine, '''
        mapping = {'a': 1}
        first, second, different = Proxy(mapping), Proxy(mapping), Proxy({'a': 2})
        for left in [first, mapping, different]:
            for right in [second, mapping, different]:
                print(left == right, left != right, left | right)
        for source in ['first < second', 'first >= mapping', 'first |= {}',
                       'first | []', '[] | first', 'hash(first)']:
            try: exec(source)
            except TypeError: print('rejected', source)
            else: raise AssertionError(source)
        class Reflected:
            def __eq__(self, other):
                other['changed'] = 1
                return other
            def __ne__(self, other):
                other['changed'] = 2
                return other
        print(first == Reflected(), mapping)
        print(first != Reflected(), mapping)
        class C: value = 42
        namespace = C.__dict__
        print(type(namespace) is Proxy, namespace['value'], vars(C) == namespace)
        C.value = 43
        print(namespace['value'])
        del C.value
        print('value' in namespace)
        try: namespace['value'] = 44
        except TypeError: print('class namespace readonly')
        for source in ['C.__dict__ = {}', 'del C.__dict__']:
            try: exec(source)
            except AttributeError: print('namespace attribute readonly')
            else: raise AssertionError(source)
        # CPython test_richcompare_evil / gh-152405: the comparison may return
        # and mutate a copy, but must not expose a builtin type's dictionary.
        leaked = vars(list) == Reflected()
        print(type(leaked) is dict, leaked['changed'], hasattr(list, 'changed'))
        leaked['probe'] = lambda self: 'probe'
        print(hasattr(list, 'probe'))
        class Custom:
            def __getitem__(self, key): return key
        custom = Custom()
        class Identity:
            def __eq__(self, other): return other
        print((Proxy(custom) == Identity()) is custom)
        mapping['self'] = first
        print(repr(first))
    ''')
    print('Mapping proxies: constructors, mapping callbacks, live class namespaces, comparisons and mutation isolation passed')


if __name__ == '__main__':
    main()
