# spec: PLS-315 26.2
# description: Programs on frozendict, each with the output CPython 3.15 gives.
from harness import *

check_program('''
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
''',
              '''dict {'a': 1, 'b': 2, 'c': 3} 3 True False True
['a', 'b', 'c'] ['c', 'b', 'a'] ['a', 'b', 'c'] [1, 2, 3] [('a', 1), ('b', 2), ('c', 3)]
['c', 'b', 'a'] [3, 2, 1] [('c', 3), ('b', 2), ('a', 1)]
mappingproxy True
1 None 9 True False
{'a': 1, 'b': 2, 'c': 3}
{'a': 1, 'b': 2, 'c': 3}
match 1 {'b': 2, 'c': 3}
dict {'a': 1, 'b': 5, 'c': 3} dict {'b': 2, 'a': 1, 'c': 3}
dict {'a': 1, 'b': 5, 'c': 3} frozendict frozendict({'b': 2, 'a': 1, 'c': 3})
dict {'a': 1, 'b': 5, 'c': 3} frozendict frozendict({'b': 2, 'a': 1, 'c': 3})
frozendict frozendict({'a': 1, 'b': 2, 'c': 3}) 3 True False True
['a', 'b', 'c'] ['c', 'b', 'a'] ['a', 'b', 'c'] [1, 2, 3] [('a', 1), ('b', 2), ('c', 3)]
['c', 'b', 'a'] [3, 2, 1] [('c', 3), ('b', 2), ('a', 1)]
mappingproxy True
({'a': 1, 'b': 2, 'c': 3},) ({'a': 1, 'b': 2, 'c': 3},)
1 None 9 True False
{'a': 1, 'b': 2, 'c': 3}
{'a': 1, 'b': 2, 'c': 3}
match 1 {'b': 2, 'c': 3}
self True
frozendict frozendict({'a': 1, 'b': 5, 'c': 3}) dict {'b': 2, 'a': 1, 'c': 3}
frozendict frozendict({'a': 1, 'b': 5, 'c': 3}) frozendict frozendict({'b': 2, 'a': 1, 'c': 3})
frozendict frozendict({'a': 1, 'b': 5, 'c': 3}) frozendict frozendict({'b': 2, 'a': 1, 'c': 3})
F F({'a': 1, 'b': 2, 'c': 3}) 3 True False True
['a', 'b', 'c'] ['c', 'b', 'a'] ['a', 'b', 'c'] [1, 2, 3] [('a', 1), ('b', 2), ('c', 3)]
['c', 'b', 'a'] [3, 2, 1] [('c', 3), ('b', 2), ('a', 1)]
mappingproxy True
({'a': 1, 'b': 2, 'c': 3},) ({'a': 1, 'b': 2, 'c': 3},)
1 None 9 True False
{'a': 1, 'b': 2, 'c': 3}
{'a': 1, 'b': 2, 'c': 3}
match 1 {'b': 2, 'c': 3}
self True
frozendict frozendict({'a': 1, 'b': 5, 'c': 3}) dict {'b': 2, 'a': 1, 'c': 3}
frozendict frozendict({'a': 1, 'b': 5, 'c': 3}) frozendict frozendict({'b': 2, 'a': 1, 'c': 3})
frozendict frozendict({'a': 1, 'b': 5, 'c': 3}) frozendict frozendict({'b': 2, 'a': 1, 'c': 3})
('missing', 7) ('missing', 7) None
frozendict({'a': [frozendict({...})]})
frozendict[str, int]
False False
False False
False False
True True
frozendict({'a': 1})
keys
get b
frozendict({'b': 4})
update False False
clear False False
pop False False
popitem False False
setdefault False False
__setitem__ False False
__delitem__ False False
__ior__ False False
''')

check_program('''
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
''',
              '''['key']
True ['key', 'value']
True
True True
True True
True
{Key(): None} frozendict({Key(): None})
['key', 'value', 'key', 'value']
True
True
''')

check_program('\nclass HashError:\n    def __hash__(self): raise KeyError(\'error\')\nclass HashTypeError:\n    def __hash__(self): raise TypeError(\'hash failure\')\nclass DerivedError(TypeError): pass\nclass HashDerivedError:\n    def __hash__(self): raise DerivedError(\'preserved\')\nd = frozendict(a=1)\nprint(frozendict.__new__(frozendict, d) is d)\nfor key in [[], HashError(), HashTypeError(), HashDerivedError()]:\n    for op in [lambda: key in d, lambda: d[key], lambda: d.get(key), lambda: frozendict([(key, 1)])]:\n        try: op()\n        except BaseException as error: print(type(error).__name__, str(error))\nfor source in ["d[\'a\'] = 2", "del d[\'a\']", "dict.__init__(d, b=3)",\n               "dict.__setitem__(d, \'a\', 2)", "dict.update(d, b=3)"]:\n    try: exec(source)\n    except TypeError: print(\'immutable\', d)\nfor source in [\'x\', \'data.append(x)\', \'x = 2\', \'del x\', \'global x\\nx = 2\', \'global x\\ndel x\']:\n    for builtins in [False, True]:\n        ns = frozendict(x=1, data=[], **({\'__builtins__\': {}} if builtins else {}))\n        try:\n            if source == \'x\': print(eval(source, ns))\n            else: exec(source, ns)\n        except BaseException as error: print(type(error).__name__, str(error))\n        print(ns[\'x\'], ns[\'data\'])\nns = frozendict(x=3, __builtins__=frozendict(answer=lambda: 4))\nlocal = {}\nexec(\'def read(): return x + answer()\', ns, local)\nprint(local[\'read\'](), local[\'read\'].__globals__ is ns)\nprint(type(\'A\', (), frozendict(x=4)).x)\nfor op in [eval, exec]:\n    try: op(\'\', frozendict())\n    except BaseException as error: print(type(error).__name__, str(error))\n',
              '''False
TypeError cannot use 'list' as a frozendict key (unhashable type: 'list')
TypeError cannot use 'list' as a frozendict key (unhashable type: 'list')
TypeError cannot use 'list' as a frozendict key (unhashable type: 'list')
TypeError cannot use 'list' as a frozendict key (unhashable type: 'list')
KeyError 'error'
KeyError 'error'
KeyError 'error'
KeyError 'error'
TypeError cannot use 'HashTypeError' as a frozendict key (hash failure)
TypeError cannot use 'HashTypeError' as a frozendict key (hash failure)
TypeError cannot use 'HashTypeError' as a frozendict key (hash failure)
TypeError cannot use 'HashTypeError' as a frozendict key (hash failure)
DerivedError preserved
DerivedError preserved
DerivedError preserved
DerivedError preserved
immutable frozendict({'a': 1})
immutable frozendict({'a': 1})
immutable frozendict({'a': 1})
immutable frozendict({'a': 1})
immutable frozendict({'a': 1})
TypeError cannot assign __builtins__ to frozendict globals
1 []
1
1 []
TypeError cannot assign __builtins__ to frozendict globals
1 []
1 [1]
TypeError cannot assign __builtins__ to frozendict globals
1 []
TypeError 'frozendict' object does not support item assignment
1 []
TypeError cannot assign __builtins__ to frozendict globals
1 []
NameError name 'x' is not defined
1 []
TypeError cannot assign __builtins__ to frozendict globals
1 []
TypeError frozendict object does not support item assignment
1 []
TypeError cannot assign __builtins__ to frozendict globals
1 []
TypeError frozendict object does not support item deletion
1 []
7 True
4
TypeError cannot assign __builtins__ to frozendict globals
TypeError cannot assign __builtins__ to frozendict globals
''')
