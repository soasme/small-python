# spec: PLS-315 15.4
# description: Programs on try statements, each with the output CPython 3.15 gives.
from harness import *

check_program("for args in [(), ('bad',), ('bad', ('path/file.py', 2, 3, 'line')),\n             ('bad', ('path/file.py', 2, 3, 'line', 2, 4)), (1, 2, 3)]:\n    error = SyntaxError(*args)\n    print(str(error), error.args, error.msg, error.filename, error.lineno,\n          error.offset, error.text, error.end_lineno, error.end_offset)\nerror.__init__('old', ('f', 2, 3, 'line', 2, 4))\nerror.__init__()\nprint(error.args, error.msg, error.filename)\nerror.__init__('new')\nprint(error.args, error.msg, error.filename)\nfor filename, line in [(None, None), (None, 0), ('', 2), (42, 2), ('f', 's'), ('f', None)]:\n    error = SyntaxError('bad')\n    error.filename = filename\n    error.lineno = line\n    print(str(error))\nfor source in ['€ = 2\\n', 'x€ = 2\\n', 'if True\\n    pass\\n']:\n    try: compile(source, 'path/file.py', 'exec')\n    except SyntaxError as error:\n        print(str(error), error.filename, error.lineno, error.offset, repr(error.text), error.end_lineno, error.end_offset)\ntry:\n    try: raise ValueError('context')\n    except ValueError: compile('€ = 1', 'file.py', 'exec')\nexcept SyntaxError as error: print(type(error.__context__).__name__)\n",
              "None () None None None None None None None\nbad ('bad',) bad None None None None None None\nbad (file.py, line 2) ('bad', ('path/file.py', 2, 3, 'line')) bad path/file.py 2 3 line None None\nbad (file.py, line 2) ('bad', ('path/file.py', 2, 3, 'line', 2, 4)) bad path/file.py 2 3 line 2 4\n1 (1, 2, 3) 1 None None None None None None\n() old f\n('new',) new f\nbad\nbad (line 0)\nbad (, line 2)\nbad (line 2)\nbad (f)\nbad (f)\ninvalid character '€' (U+20AC) (file.py, line 1) path/file.py 1 1 '€ = 2' 1 1\ninvalid character '€' (U+20AC) (file.py, line 1) path/file.py 1 2 'x€ = 2' 1 2\nexpected ':' (file.py, line 1) path/file.py 1 8 'if True\\n' 1 9\nValueError\n")

check_program('''µ = 42
𝔘𝔫𝔦𝔠𝔬𝔡𝔢 = 1
print(μ, Unicode, 'µ' in globals(), 'μ' in globals())
def résumé(K=3, *, µ=4): return K, μ
print(résumé(K=1, µ=2), résumé.__name__)
try: résumé(**{'µ': 3})
except TypeError: print('string keyword is not normalized')
class 𝔘:
    __µ = 5
    def read(self): return self.__μ
print(U.__name__, U().read(), U._U__μ)
print([µ for µ in range(3)], µ)
ｉｆ = 7
print(globals()['if'])
''',
              '''42 1 False True
(1, 2) résumé
string keyword is not normalized
U 5 5
[0, 1, 2] 42
7
''')

check_program('''# Default deletion and readonly globals from CPython test_funcattrs.
def f(a=1, *, b=2): return a, b
print(f())
del f.__defaults__
print(f.__defaults__, f(3))
try: f()
except TypeError: print('positional default removed')
print(delattr(f, '__kwdefaults__'), f.__kwdefaults__)
try: f(3)
except TypeError: print('keyword default removed')
print(f(3, b=4))
for name in ['__defaults__', '__kwdefaults__', '__module__', '__doc__', '__annotations__']:
    delattr(f, name)
    print(name, getattr(f, name))
for name in ['__name__', '__qualname__', '__dict__', '__code__', '__type_params__']:
    try: delattr(f, name)
    except TypeError: print('required', name)
for name in ['__globals__', '__builtins__', '__closure__']:
    try: setattr(f, name, {})
    except AttributeError: print('readonly assignment', name)
    try: delattr(f, name)
    except AttributeError: print('readonly deletion', name)
f.extra = [f]
print(delattr(f, 'extra'), hasattr(f, 'extra'))
try: delattr(f, 'extra')
except AttributeError: print('missing attribute')
wrapped = staticmethod(f)
wrapped.extra = 3
del wrapped.extra
print(hasattr(wrapped, 'extra'))
''',
              '''(1, 2)
None (3, 2)
positional default removed
None None
keyword default removed
(3, 4)
__defaults__ None
__kwdefaults__ None
__module__ None
__doc__ None
__annotations__ {}
required __name__
required __qualname__
required __dict__
required __code__
required __type_params__
readonly assignment __globals__
readonly deletion __globals__
readonly assignment __builtins__
readonly deletion __builtins__
readonly assignment __closure__
readonly deletion __closure__
None False
missing attribute
False
''')

check_program('''# Invalid exception factory results from CPython test_raise.
class Mortal(Exception):
    def __new__(cls, *args, **kwargs): return ['mortal']
    def __init__(self, *args): print('must not initialize')
print(Mortal(1))
try: raise Mortal
except TypeError: print('invalid exception factory')
try: raise IndexError from Mortal
except TypeError: print('invalid cause factory')
class Custom(Exception):
    def __new__(cls, *args, **kwargs):
        print('allocate', args, kwargs)
        return BaseException.__new__(cls, *args, **kwargs)
    def __init__(self, *args, **kwargs):
        print('initialize', self.args, kwargs)
        BaseException.__init__(self, *args)
error = Custom(1, named=2)
print(error.args, error.__cause__, error.__context__, error.__suppress_context__)
for cls in [int, list, Exception]:
    try: object.__new__(cls)
    except TypeError: print('unsafe allocator')
try: BaseException.__new__(object)
except TypeError: print('wrong exception type')
''',
              '''['mortal']
invalid exception factory
invalid cause factory
allocate (1,) {'named': 2}
initialize (1,) {'named': 2}
(1,) None None False
unsafe allocator
unsafe allocator
unsafe allocator
wrong exception type
''')

check_program("calls = []\nclass Get:\n    def __get__(self, instance, owner):\n        calls.append(('get', instance is None, owner is C))\n        def create(cls, value):\n            calls.append(('create', cls is C, value))\n            return object.__new__(cls)\n        return create\nclass C:\n    __new__ = Get()\n    def __init__(self, value=0): calls.append(('init', value))\nC(3)\nprint(calls)\ndef other(cls): return 42\nC.__new__ = other\nprint(C())\ndel C.__new__\nprint(type(C()) is C, calls)\nclass InitError:\n    def __init__(self): return 1\ntry: InitError()\nexcept TypeError: print('invalid initializer result')\ndef keywords(a=1, **kw): return a, kw\nprint(keywords(**{'a\\x00extra': 2}))\n",
              "[('get', True, True), ('create', True, 3), ('init', 3)]\n42\nTrue [('get', True, True), ('create', True, 3), ('init', 3), ('init', 0)]\ninvalid initializer result\n(1, {'a\\x00extra': 2})\n")

check_program('''class Clear:
    def __eq__(self, other):
        items.clear()
        return answer
for answer in [False, True]:
    for method in ['index', 'remove', 'count']:
        items = [Clear(), 1, 2]
        try: print(method, getattr(items, method)(None), items)
        except ValueError: print(method, 'missing', items)
class Bad:
    def __eq__(self, other): raise ValueError('comparison')
for method in ['index', 'remove', 'count']:
    try: getattr([Bad()], method)(None)
    except ValueError as error: print(method, error)
''',
              '''index missing []
remove missing []
count 0 []
index 0 []
remove None []
count 1 []
index comparison
remove comparison
count comparison
''')

check_program('''items = [(2, 'a'), (1, 'b'), (2, 'c'), (1, 'd')]
def key(item): print('key', item, items); return item[0]
print(items.sort(key=key, reverse=True), items)
for action in ['append', 'append-pop', 'clear', 'slice', 'reverse', 'sort', 'extend']:
    items = [3, 1, 2]
    def change(x):
        if action == 'append': items.append(42)
        if action == 'append-pop': items.append(42); items.pop()
        if action == 'clear': items.clear()
        if action == 'slice': del items[:]
        if action == 'reverse': items.reverse()
        if action == 'sort': items.sort()
        if action == 'extend': items.extend([])
        return x
    try: print(action, items.sort(key=change), items)
    except ValueError as error: print(action, error, items)
items = [3, 2, 1]
def fail(x):
    if x == 2: raise ValueError('key')
    return x
try: items.sort(key=fail)
except ValueError as error: print(error, items)
''',
              '''key (2, 'a') []
key (1, 'b') []
key (2, 'c') []
key (1, 'd') []
None [(2, 'a'), (2, 'c'), (1, 'b'), (1, 'd')]
append list modified during sort [1, 2, 3]
append-pop list modified during sort [1, 2, 3]
clear None [1, 2, 3]
slice None [1, 2, 3]
reverse None [1, 2, 3]
sort None [1, 2, 3]
extend None [1, 2, 3]
key [3, 2, 1]
''')

check_program('''def f(a, b=2, /, c=3, *, d=4): return a, b, c, d
print(f.__defaults__, f.__kwdefaults__, f(1))
f.__defaults__ = (10, 20, 30)
f.__kwdefaults__['d'] = 40
print(f(), f(1, c=5))
f.__kwdefaults__ = {'d': 50, 'unused': 99}
print(f())
f.__defaults__ = (9, 10, 20, 30)
print(f())
f.__defaults__ = None
f.__kwdefaults__ = None
print(f(1, 2, 3, d=4))
try: f(1, 2, 3)
except TypeError: print('missing keyword default')
for name, value in [('__defaults__', []), ('__kwdefaults__', ())]:
    try: setattr(f, name, value)
    except TypeError: print('invalid defaults')
code = f.__code__
print(code is f.__code__, code.co_name, code.co_qualname)
print(code.co_argcount, code.co_posonlyargcount, code.co_kwonlyargcount)
f.__name__ = 'renamed'
print(code.co_name)
''',
              '''(2, 3) {'d': 4} (1, 2, 3, 4)
(10, 20, 30, 40) (1, 20, 5, 40)
(10, 20, 30, 50)
(10, 20, 30, 50)
(1, 2, 3, 4)
missing keyword default
invalid defaults
invalid defaults
True f f
3 2 1
f
''')

check_program('''calls = []
def key(item): calls.append(item); return item[0]
values = [(2, 'a'), (1, 'b'), (2, 'c'), (1, 'd')]
print(sorted(values, key=key), calls)
calls = []
print(sorted(values, key=key, reverse=True), calls)
print(values, sorted(values, key=None, reverse=False))
class Less:
    def __init__(self, value): self.value = value
    def __lt__(self, other): return self.value < other.value
print([x.value for x in sorted([Less(3), Less(1), Less(2)])])
def fail(item):
    calls.append(item)
    if item == 2: raise ValueError('key')
    return item
calls = []
try: sorted([3, 2, 1], key=fail)
except ValueError as error: print(error, calls)
class Fail:
    def __lt__(self, other): raise ValueError('comparison')
try: sorted([Fail(), Fail()])
except ValueError as error: print(error)
print(sorted([], key=42), sorted([1], key=None))
''',
              '''[(1, 'b'), (1, 'd'), (2, 'a'), (2, 'c')] [(2, 'a'), (1, 'b'), (2, 'c'), (1, 'd')]
[(2, 'a'), (2, 'c'), (1, 'b'), (1, 'd')] [(2, 'a'), (1, 'b'), (2, 'c'), (1, 'd')]
[(2, 'a'), (1, 'b'), (2, 'c'), (1, 'd')] [(1, 'b'), (1, 'd'), (2, 'a'), (2, 'c')]
[1, 2, 3]
key [3, 2]
comparison
[] [1]
''')

check_program("exec(compile('1; None; 2', '<single>', 'single'))\nexec(compile('(1\\n+2); 4', '<single>', 'single'))\nexec(compile('if True:\\n    3\\n    4\\n', '<single>', 'single'))\nprint(eval(compile('5', '<single>', 'single')))\nexec(compile('def f():\\n    9\\n', '<single>', 'single'))\nprint(f())\nfor source in ['', '1\\n2', 'if True:\\n    1\\n2']:\n    try: compile(source, '<single>', 'single')\n    except SyntaxError: print('invalid single input')\n",
              '''None
None
invalid single input
invalid single input
invalid single input
''')

check_program('''events = []
class Left:
    def __eq__(self, other): events.append('left eq'); return NotImplemented
    def __lt__(self, other): events.append('left lt'); return NotImplemented
class Right(Left):
    def __eq__(self, other): events.append('right eq'); return ['equal']
    def __gt__(self, other): events.append('right gt'); return ['greater']
left = Left(); right = Right()
print(left == right, events); events = []
print(left != right, events); events = []
print(left < right, events); events = []
class Other:
    def __ne__(self, other): events.append('other ne'); return NotImplemented
print(left != Other(), events)
class All:
    def __eq__(self, other): return True
print(All() in [1], [1] == [All()], range(10).count(All()), range(10).index(All()))
class Container:
    def __contains__(self, item): return item == 42
print(42 in Container(), 3 not in Container())
print(All.__hash__ is None)
try: {All(): 1}
except TypeError: print('unhashable')
''',
              '''['equal'] ['right eq']
False ['right eq']
['greater'] ['right gt']
True ['left eq', 'other ne']
True True 10 0
True True
True
unhashable
''')

check_program('''nan = float('nan')
print(nan == nan, nan in [nan], {nan: 42}[nan], [nan] == [nan])
print(slice(nan) == slice(nan), slice(nan) <= slice(nan))
class Bad:
    def __eq__(self, other): raise ValueError('comparison')
try: [Bad()] == [Bad()]
except ValueError as error: print(error)
bad = slice(Bad())
print(bad == bad)
try: bad == slice(Bad())
except ValueError as error: print(error)
class Clear:
    def __eq__(self, other):
        del left[:]
        del right[:]
        return False
    def __lt__(self, other): return True
left = [Clear(), 1]; right = [Clear(), 2]
print(left < right, left, right)
left = [Clear(), 1]; right = [Clear(), 2]
print(left == right, left, right)
class Key:
    def __hash__(self): return 0
    def __eq__(self, other):
        del mapping[self]
        return True
key = Key(); mapping = {key: 1}
print(Key() in mapping, len(mapping))
''',
              '''False True 42 True
True True
comparison
True
comparison
False [] []
True [] []
False 0
''')

check_program('m = memoryview(b"abcdef")\nprint(len(m), m[1], bytes(m[1:3]), m.tolist()[:3], m.readonly, m.format, m.itemsize, m.shape, m.strides, m[-1])\nprint(m == b"abcdef", m.hex(), bytes(m[::2]), hash(memoryview(b"ab")) == hash(b"ab"), repr(m)[:12])\nba = bytearray(b"hello")\nv = memoryview(ba)\nv[0] = 72; v[1:3] = b"EL"\nprint(ba, b"x" + v, b"-".join([v, b"z"]), str(v, "ascii"), b"HEllo".startswith((b"q", v[:2])))\nfor mutate in (lambda: ba.append(1), lambda: ba.pop(), lambda: ba.extend(b"ab"), lambda: ba.clear()):\n    try: mutate()\n    except BufferError as e: print("BufferError", e)\nba[0] = 104; print(v[0])\nv.release(); ba.append(33); print(ba)\ntry: v[0]\nexcept ValueError as e: print(e)\nc = memoryview(b"\\x01\\x00\\x02\\x00\\x03\\x00\\x04\\x00").cast("H")\nprint(c.tolist(), c.format, c.nbytes, len(c), c.cast("B").tolist(), c.cast("B", (2, 4)).tolist())\nwith memoryview(bytearray(b"q")) as q: print(q[0], q.toreadonly().readonly, q.obj)\ntry: memoryview(b"ab")[0] = 1\nexcept TypeError as e: print(e)\ntry: memoryview(bytearray(b"ab"))[0] = 300\nexcept ValueError as e: print(e)\ntry: memoryview("text")\nexcept TypeError as e: print(e)\nr = bytearray(b"rw").__buffer__(0); print(type(r).__name__, r.readonly)\ntry: b"ro".__buffer__(1)\nexcept BufferError as e: print(e)\nclass B:\n    def __buffer__(self, flags): return memoryview(b"custom")\nprint(bytes(memoryview(B())))\n',
              '''6 98 b'bc' [97, 98, 99] True B 1 (6,) (1,) 102
True 616263646566 b'ace' True <memory at 0
bytearray(b'HELlo') b'xHELlo' b'HELlo-z' HELlo True
BufferError Existing exports of data: object cannot be re-sized
BufferError Existing exports of data: object cannot be re-sized
BufferError Existing exports of data: object cannot be re-sized
BufferError Existing exports of data: object cannot be re-sized
104
bytearray(b'hELlo!')
operation forbidden on released memoryview object
[1, 2, 3, 4] H 8 4 [1, 0, 2, 0, 3, 0, 4, 0] [[1, 0, 2, 0], [3, 0, 4, 0]]
113 True bytearray(b'q')
cannot modify read-only memory
memoryview: invalid value for format 'B'
memoryview: a bytes-like object is required, not 'str'
memoryview False
Object is not writable.
b'custom'
''')

check_program('''print(sentinel, type(sentinel), sentinel.__doc__ is not None)
s = sentinel('MISSING')
print(repr(s), str(s), type(s), s.__name__, s.__module__, bool(s), hash(s) == hash(s), s == s, s is s, f"{s}")
print(s.__copy__() is s, s.__deepcopy__({}) is s)
def p(f):
    try: print(repr(f()))
    except Exception as e: print(type(e).__name__+':', e)
p(lambda: sentinel()); p(lambda: sentinel(1)); p(lambda: sentinel('a', 'b')); p(lambda: sentinel(name='x'))
p(lambda: s.__reduce__())
p(lambda: type('X', (sentinel,), {}))
p(lambda: s.x)
def setx(): s.x = 1
p(setx)
p(lambda: s | int); p(lambda: int | s); p(lambda: sentinel('A', module='m').__module__)
p(lambda: s.__name__ == 'MISSING')
p(lambda: sentinel('A') == sentinel('A'))
p(lambda: (s | None).__args__)
def f(): return sentinel('In').__module__
p(f)
p(lambda: s < s)
''',
              '''<class 'sentinel'> <class 'type'> True
MISSING MISSING <class 'sentinel'> MISSING __main__ True True True True MISSING
True True
TypeError: sentinel() takes exactly 1 positional argument (0 given)
TypeError: sentinel() argument 1 must be str, not int
TypeError: sentinel() takes exactly 1 positional argument (2 given)
TypeError: sentinel() takes exactly 1 positional argument (0 given)
'MISSING'
TypeError: type 'sentinel' is not an acceptable base type
AttributeError: 'sentinel' object has no attribute 'x'
AttributeError: 'sentinel' object has no attribute 'x' and no __dict__ for setting new attributes
MISSING | int
int | MISSING
TypeError: sentinel() got an unexpected keyword argument 'module'
True
False
(MISSING, <class 'NoneType'>)
'__main__'
TypeError: '<' not supported between instances of 'sentinel' and 'sentinel'
''')

check_program('''class B: pass
B.__abstractmethods__ = frozenset({"z", "a"})
try: B()
except TypeError as e: print(e)
B.__abstractmethods__ = ()
print(type(B()).__name__)
class C(B): pass
B.__abstractmethods__ = {"q"}
print(type(C()).__name__)
''',
              '''Can't instantiate abstract class B without an implementation for abstract methods 'a', 'z'
B
C
''')

check_program('''def t(src):
    try: r = compile(src, "<s>", "eval"); print("ok")
    except (SyntaxError, RecursionError, MemoryError) as e: print(type(e).__name__, e.msg if isinstance(e, SyntaxError) else e)
for n in (100, 199, 200, 201):
    t("[" * n + "]" * n)
    t("(" * n + "1" + ")" * n)
for n in (100, 1000, 3000):
    t("-" * n + "1")
    t("not " * n + "1")
    t("2" + "**2" * n)
    t("lambda: " * n + "1")
    t("x" + ".y" * n)
    t("x" + "[0]" * n)
    t("x" + "()" * n)
''',
              '''ok
ok
ok
ok
ok
ok
SyntaxError too many nested parentheses
SyntaxError too many nested parentheses
ok
ok
ok
ok
ok
ok
ok
ok
ok
ok
ok
ok
ok
ok
ok
ok
MemoryError Parser stack overflowed - Python source too complex to parse
MemoryError Parser stack overflowed - Python source too complex to parse
ok
ok
ok
''')

check_program('''class A: pass
class B(A): pass
class E(Exception): pass
class S: __slots__=()
class T(S): pass
class D:
    "doc"
    x = 1
class I(int): pass
class L(list): pass
for k in (A,B,E,S,T,D,I,L): print(k.__name__, list(k.__dict__))
print(A.__dict__["__dict__"], A.__dict__["__weakref__"], A().__weakref__)
a=A(); d=A.__dict__["__dict__"]; print(d.__get__(a), d.__name__, d.__objclass__)
d.__set__(a, {"q": 1}); print(a.q)
try: d.__get__(1)
except (TypeError, AttributeError) as e: print(type(e).__name__, e)
try: d.__set__(a, 1)
except (TypeError, AttributeError) as e: print(type(e).__name__, e)
try: d.__delete__(a)
except (TypeError, AttributeError) as e: print(type(e).__name__, e)
print(a.__dict__)
print(vars(B()), "__dict__" in dir(A()), "__weakref__" in dir(A))
w = A.__dict__["__weakref__"]
print(type(A.__dict__["__dict__"]).__name__, w.__objclass__, w.__get__(A()), w.__name__)
try: w.__set__(A(), 1)
except Exception as e: print(type(e).__name__, e)
class S2: __slots__ = ("__dict__",)
class S3: __slots__ = ("__weakref__", "a")
print(list(S2.__dict__), list(S3.__dict__), S3.__dict__["__weakref__"])
class M(type): pass
print(list(M.__dict__))
a = A(); a.__dict__ = {"z": 2}; print(a.z)
try: A.__dict__["__dict__"].__set__(a, None)
except Exception as e: print(type(e).__name__, e)
''',
              '''A ['__module__', '__firstlineno__', '__static_attributes__', '__dict__', '__weakref__', '__doc__']
B ['__module__', '__firstlineno__', '__static_attributes__', '__doc__']
E ['__module__', '__firstlineno__', '__static_attributes__', '__weakref__', '__doc__']
S ['__module__', '__firstlineno__', '__slots__', '__static_attributes__', '__doc__']
T ['__module__', '__firstlineno__', '__static_attributes__', '__dict__', '__weakref__', '__doc__']
D ['__module__', '__firstlineno__', '__doc__', 'x', '__static_attributes__', '__dict__', '__weakref__']
I ['__module__', '__firstlineno__', '__static_attributes__', '__dict__', '__doc__']
L ['__module__', '__firstlineno__', '__static_attributes__', '__dict__', '__weakref__', '__doc__']
<attribute '__dict__'> <attribute '__weakref__'> None
{} __dict__ <class 'object'>
1
AttributeError This object has no __dict__
TypeError __dict__ must be set to a dictionary, not a 'int'
{}
{} True True
getset_descriptor <class 'object'> None __weakref__
AttributeError attribute '__weakref__' of 'object' objects is not writable
['__module__', '__firstlineno__', '__slots__', '__static_attributes__', '__dict__', '__doc__'] ['__module__', '__firstlineno__', '__slots__', '__static_attributes__', '__weakref__', 'a', '__doc__'] <attribute '__weakref__'>
['__module__', '__firstlineno__', '__static_attributes__', '__doc__']
2
TypeError __dict__ must be set to a dictionary, not a 'NoneType'
''')

check_program('class __future__: CO_FUTURE_BARRY_AS_BDFL = 0x400000\ndef t(src, flags=0):\n    try:\n        compile(src, "<s>", "exec", flags); print("ok")\n    except SyntaxError as e: print(repr(e.msg), e.lineno, e.offset, e.end_lineno, e.end_offset, repr(e.text))\nt("1 <> 2")\nt("1 <> 2", __future__.CO_FUTURE_BARRY_AS_BDFL)\nt("1 != 2", __future__.CO_FUTURE_BARRY_AS_BDFL)\nt("from __future__ import barry_as_FLUFL\\n1 <> 2")\nt("from __future__ import barry_as_FLUFL\\n1 != 2")\nt("from __future__ import braces")\nt("from __future__ import nope")\nt("from __future__ import nope, braces")\nt("x = 1\\nfrom __future__ import annotations")\nt(\'"""doc"""\\nfrom __future__ import annotations\\nfrom __future__ import division\')\nt(\'"""doc"""\\n"""x"""\\nfrom __future__ import annotations\')\nt(\'def f():\\n    from __future__ import annotations\')\nt(\'from __future__ import (annotations, division,)\')\nt(\'from __future__ import annotations as a\')\nt(\'from __future__ import *\')\nt(\'import __future__\\nfrom __future__ import annotations\')\nt(\'from .__future__ import annotations\')\nt(\'if 1:\\n    from __future__ import annotations\')\nt(\'from __future__ import annotations; x = 1; from __future__ import division\')\nt(\'from __future__ import barry_as_FLUFL\\ndef f(a: 1 <> 2): pass\')\nt(\'a <> b\', 0)\nt(\'a < > b\', 0)\nt(\'class A:\\n    from __future__ import annotations\')\n',
              '"invalid syntax.  Maybe you meant \'!=\' instead of \'<>\'?" 1 3 1 5 \'1 <> 2\\n\'\nok\n"with Barry as BDFL, use \'<>\' instead of \'!=\'" 1 3 1 5 \'1 != 2\\n\'\nok\n"with Barry as BDFL, use \'<>\' instead of \'!=\'" 2 3 2 5 \'1 != 2\\n\'\n\'not a chance\' 1 24 1 30 None\n\'future feature nope is not defined\' 1 24 1 28 None\n\'future feature nope is not defined\' 1 24 1 28 None\n\'from __future__ imports must occur at the beginning of the file\' 2 1 2 35 None\nok\n\'from __future__ imports must occur at the beginning of the file\' 3 1 3 35 None\n\'from __future__ imports must occur at the beginning of the file\' 2 5 2 39 None\nok\nok\n\'future feature * is not defined\' 1 24 1 25 None\n\'from __future__ imports must occur at the beginning of the file\' 2 1 2 35 None\nok\n\'from __future__ imports must occur at the beginning of the file\' 2 5 2 39 None\n\'from __future__ imports must occur at the beginning of the file\' 1 44 1 75 None\nok\n"invalid syntax.  Maybe you meant \'!=\' instead of \'<>\'?" 1 3 1 5 \'a <> b\\n\'\n\'invalid syntax\' 1 5 1 6 \'a < > b\\n\'\n\'from __future__ imports must occur at the beginning of the file\' 2 5 2 39 None\n')

check_program('for s in ["return 1", "async for x in y: pass", "nonlocal x", "def f():\\n    x = 1\\n    global x"]:\n    try: compile(s, "<s>", "exec")\n    except SyntaxError as e: print(e.msg, repr(e.text))\n',
              ''''return' outside function None
'async for' outside async function None
nonlocal declaration not allowed at module level None
name 'x' is assigned to before global declaration None
''')

check_program('''class operator:
    lt = __lt__ = staticmethod(lambda a, b: a < b)
    eq = staticmethod(lambda a, b: a == b)
class V:
    def __init__(s, d): s.d = d
    def __bool__(s): raise TypeError("no bool")
    def __lt__(s, o): return V([1])
    def __eq__(s, o): return V([2])
    def __gt__(s, o): return V([3])
    def __repr__(s): return "V%r" % s.d
for f in (lambda a,b: a<b, operator.lt, operator.__lt__, lambda a,b: a==b, operator.eq, lambda a,b: a>b):
    for a, b in ((list(range(3)), V(1)), (V(1), [1]), (V(1), V(2))):
        try: print(f(a, b))
        except TypeError as e: print("TE", e)
''',
              '''V[3]
V[1]
V[1]
V[3]
V[1]
V[1]
V[3]
V[1]
V[1]
V[2]
V[2]
V[2]
V[2]
V[2]
V[2]
V[1]
V[3]
V[3]
''')
