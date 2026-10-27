# spec: PLS-315 15.4
# description: Programs on try statements, each with the output CPython 3.15 gives.
from harness import *

check_program('''class A:
    __slots__ = ("x", "y")
a = A()
try: a.x
except AttributeError as e: print(e)
a.x = 1; print(a.x)
del a.x
try: del a.x
except AttributeError as e: print(e)
print(type(A.__dict__["x"]).__name__, A.__dict__["x"], A.x.__get__(None, A) is A.x)
try: a.__dict__
except AttributeError as e: print(e)
class B(A): pass
b = B(); b.z = 3; print(b.__dict__)
class C:
    __slots__ = ("__dict__", "w")
c = C(); c.k = 1; c.w = 2; print(c.__dict__)
class D:
    __slots__ = "one"
print(D.__slots__, hasattr(D(), "__weakref__"))
try:
    class E:
        __slots__ = ("x",)
        x = 1
except ValueError as e: print(e)
try:
    class F:
        __slots__ = ("1x",)
except TypeError as e: print(e)
class G:
    __slots__ = ("__private",)
print([k for k in G.__dict__ if "private" in k])
''',
              ''''A' object has no attribute 'x'
1
x
member_descriptor <member 'x' of 'A' objects> True
'A' object has no attribute '__dict__'
{'z': 3}
{'k': 1}
one False
'x' in __slots__ conflicts with class variable
__slots__ must be identifiers
['_G__private']
''')

check_program('''for base in (int, bytes, tuple, str, float, list, dict, BaseException):
    try:
        class X(base): __slots__ = ("a",)
        print(base.__name__, "ok", hasattr(X(), "__dict__"))
    except TypeError as e: print(e)
class O: __slots__ = ("a",)
o = O()
try: del o.b
except AttributeError as e: print(e)
try: o.__dict__ = {}
except AttributeError as e: print(e)
try: vars(o)
except TypeError as e: print(e)
class P: __slots__ = ("p",)
class Q: __slots__ = ("q",)
try:
    class R(P, Q): pass
except TypeError as e: print(e)
class R2(P, O.__mro__[-1]): pass
class E: __slots__ = ()
class F(P, E): pass
try:
    class G: __slots__ = (1,)
except TypeError as e: print(e)
try:
    class H(BaseException): __slots__ = ("__dict__",)
except TypeError as e: print(e)
class I: __slots__ = ("__weakref__",)
class J(I): __slots__ = ("x",)
try:
    class K(J): __slots__ = ("__weakref__",)
except TypeError as e: print(e)
class L: __slots__ = {"a": "doc a"}
print(L.a.__doc__, L.__slots__)
class M: __slots__ = ["m"]
print(M.__slots__, O.a.__objclass__, O.a.__name__)
try: O.a.__get__(1)
except TypeError as e: print(e)
o.a = 5; print(o.a, getattr(o, "a"))
print(type(O.__dict__["a"]), repr(type(O.__dict__["a"]).__name__))
try:
    class N: __slots__ = ("a", "a")
except Exception as e: print(type(e).__name__, e)
''',
              '''arbitrary __slots__ not supported for subtype of 'int'
arbitrary __slots__ not supported for subtype of 'bytes'
tuple ok False
str ok False
float ok False
list ok False
dict ok False
BaseException ok True
'O' object has no attribute 'b' and no __dict__ for setting new attributes
'O' object has no attribute '__dict__' and no __dict__ for setting new attributes
vars() argument must have __dict__ attribute
multiple bases have instance lay-out conflict
__slots__ items must be strings, not 'int'
__dict__ slot disallowed: we already got one
__weakref__ slot disallowed: we already got one
None {'a': 'doc a'}
['m'] <class '__main__.O'> a
descriptor 'a' for 'O' objects doesn't apply to a 'int' object
5 5
<class 'member_descriptor'> 'member_descriptor'
''')

check_program('''def f(self): return self
class A:
    def m(self): pass
for o in [f, A().m, len, str.join, object.__init__, (1).__add__]:
    print(type(o).__name__, hasattr(o, "__get__"), hasattr(o, "__set__"))
a = A()
print(f.__get__(a).__self__ is a, f.__get__(None, A) is f, f.__get__(a, A).__func__ is f)
try: f.__get__()
except Exception as e: print(type(e).__name__, e)
try: f.__get__(None, None)
except Exception as e: print(type(e).__name__, e)
try: f.__get__(None)
except Exception as e: print(type(e).__name__, e)
print(str.join.__get__("x")(["a", "b"]), object.__init__.__get__(a)())
print(str.join.__get__(None, str) is str.join)
try: str.join.__get__(1)
except Exception as e: print(type(e).__name__, e)
m = a.m
print(m.__get__(1) is m)
print(type(f).__get__(f, a).__self__ is a)
class B:
    def __repr__(self): return "B-repr"
    def bit_length(self): return "B"
class X(int, B): pass
print(repr(X(3)), X.__repr__, X(3).bit_length(), X.bit_length, X.__repr__ in (int.__repr__, object.__repr__))
''',
              '''function True False
method True False
builtin_function_or_method False False
method_descriptor True False
wrapper_descriptor True False
method-wrapper False False
True True True
TypeError __get__ expected at least 1 argument, got 0
TypeError __get__(None, None) is invalid
TypeError __get__(None, None) is invalid
axb None
True
TypeError descriptor 'join' for 'str' objects doesn't apply to a 'int' object
True
True
3 <slot wrapper '__repr__' of 'int' objects> 2 <method 'bit_length' of 'int' objects> True
''')

check_program('''log = []
class Manager:
    def __enter__(self): return [1]
    def __exit__(self, kind, value, traceback):
        log.append(kind is ValueError)
        return True
with Manager() as (a, b):
    print('wrong')
print(log)
a = [0, 1, 2]; d = {'a': 1}; del a[-1], d['a']; print(a, d)
x = 1
def f():
    x = 2
    del x
    try:
        return x
    except UnboundLocalError:
        return 3
print(f(), x)
''',
              '''[True]
[0, 1] {}
3 1
''')

check_program('''class Problem(ValueError):
    pass
log = []
def f():
    try:
        try:
            raise Problem('detail')
        except LookupError:
            log.append('wrong')
        except (TypeError, ValueError) as error:
            log.append(error.args[0])
            raise
        finally:
            log.append('inner finally')
    except Problem:
        return 42
    finally:
        log.append('outer finally')
print(f(), log)
''',
              '''42 ['detail', 'inner finally', 'outer finally']
''')

check_program('''def f():
    try:
        return 1
    finally:
        return 2
def g():
    try:
        1 / 0
    finally:
        return 3
print(f(), g())
for i in range(3):
    try:
        if i == 0:
            continue
        break
    finally:
        print(i)
''',
              '''2 3
0
1
''')

check_program('''try:
    1 / 0
except ArithmeticError as e:
    print('caught')
else:
    print('wrong')
try:
    e
except NameError:
    print('deleted')
''',
              '''caught
deleted
''')

check_program('''def stop():
    raise StopIteration
g = (stop() for x in range(1))
try:
    next(g)
except RuntimeError:
    print('converted')
print(list(g))
''',
              '''converted
[]
''')

check_program('''print(1, 2, sep=':', end='!')
print(3, 4, sep=None, end=None, flush=True)
class File:
    def write(self, text): print('write', repr(text))
    def flush(self): print('flush')
print(1, 2, file=File(), sep='-', end='.', flush=True)
class Bad:
    def __str__(self): raise ValueError('bad')
try:
    print('before', Bad(), sep=':')
except ValueError:
    print('caught')
''',
              '''1:2!3 4
write '1-2.'
caught
''')

check_program('''x = 10
def global_mutate():
    global x
    x = 20
    del x
global_mutate()
try:
    print(x)
except NameError:
    print('global deleted')
def outer():
    x = 1
    def clear():
        nonlocal x
        del x
    def get(): return x
    def set():
        nonlocal x
        x = 42
    clear()
    try:
        get()
    except NameError:
        print('cell cleared')
    set()
    return get
print(outer()())
''',
              '''global deleted
cell cleared
42
''')

check_program('''class C:
    def __init__(self, __value): self.__value = __value
    def __read(self): return self.__value
    def read(self): return self.__read()
    def change(self, __value): self.__value = __value
c = C(10)
print(c.read(), c._C__value, c._C__read())
c.change(_C__value=20)
print(c.read())
try:
    c.change(__value=30)
except TypeError:
    print('keyword not mangled')
class __D:
    __x = 42
print(__D.__name__, __D._D__x)
class ___:
    __x = 43
print(___.__x)
class Outer:
    class __Inner:
        __x = 44
    def get(self): return self.__Inner._Inner__x
print(Outer._Outer__Inner.__name__, Outer().get())
''',
              '''10 10 10
20
keyword not mangled
__D 42
43
__Inner 44
''')

check_program('''original = TypeError
g = {}
exec("__builtins__['TypeError'] = 9; __builtins__['BaseException'] = 9", g)
try:
    len(1)
except original as error:
    print(type(error) is original)
''',
              '''True
''')

check_program('''class L(list):
    def total(self): return sum(self)
l = L([3, 1, 2])
print(l, len(l), l.total(), l[0], l[-1], l[1:], type(l).__name__, isinstance(l, list))
l.append(5); l.sort(); print(l, type(l) is L, 5 in l, list(l), bool(L()), bool(l))
l += [7]; print(type(l).__name__, l)
l[0] = 9; del l[1]; print(l, l == [9, 3, 5, 7], l + [1], type(l + [1]).__name__, sorted(l))
class D(dict):
    def __missing__(self, key): return key * 2
d = D(a=1)
print(d, d["a"], d["zz"], len(d), "a" in d, d.get("q"), list(d.items()), type(d.copy()).__name__)
d["b"] = 2; print(d, D({1: 2}, x=3))
class Counter(dict):
    def __init__(self, items):
        super().__init__()
        for item in items: self[item] = self.get(item, 0) + 1
print(Counter("abca"))
class MyInt(int):
    def double(self): return self * 2
m = MyInt(21)
print(m, m + 1, m.double(), type(m + 1).__name__, m == 21, hash(m) == hash(21), {m: 1}[21], int(m), float(m), m > 3, -m, f"{m:>5}", str(m), repr(m))
print(MyInt("ff", 16), MyInt(), range(MyInt(3)), [0, 1, 2][MyInt(1)], m.bit_length(), m.real, abs(m), divmod(m, 4))
class Name(str):
    def shout(self): return self.upper() + "!"
n = Name("bob")
print(n, repr(n), n.shout(), n + "x", len(n), n[0], n == "bob", {"bob": 1}[n], "-".join([n, n]), n.split("o"), f"{n}|{n!r}|{n:>5}", "%s" % n, str(n) == "bob", type(str(n)).__name__)
class P(tuple):
    def __new__(cls, x, y): return super().__new__(cls, (x, y))
    @property
    def x(self): return self[0]
p = P(1, 2)
print(p, p.x, len(p), p == (1, 2), hash(p) == hash((1, 2)), p + (3,), type(p).__name__)
x, y = p; print(x, y)
class F(float): pass
print(F(1.5), F("2.5") + 1, F(3) * 2, round(F(2.567), 2), F(1.0).is_integer())
class S(set): pass
s = S([1, 2]); s.add(3); print(sorted(s), len(s), s | {9} == {1, 2, 3, 9})
class FS(frozenset): pass
print(sorted(FS([1, 2])), hash(FS([1])) == hash(frozenset([1])))
class B(bytes): pass
print(B(b"ab"), B(b"ab").decode(), B([65]), len(B(b"xyz")))
class BA(bytearray): pass
ba = BA(b"ab"); ba.append(99); print(ba, len(ba))
for bad in ["class X(bool): pass", "class X(range): pass", "class X(list, dict): pass", "class X(int, str): pass", "class X(Exception, int): pass"]:
    try: exec(bad); print("ok")
    except TypeError as e: print("TypeError", e)
try: hash(L())
except TypeError as e: print(e)
try: list.__new__(int)
except TypeError as e: print(e)
class Override(list):
    def __len__(self): return 42
    def __getitem__(self, i): return "item"
    def __repr__(self): return "Override!"
o = Override([1, 2])
print(len(o), o[0], o, str(o), list(o), bool(Override()))
class Eq(int):
    def __eq__(self, other): return True
    __hash__ = int.__hash__
print(Eq(1) == 5, Eq(1) != 5, hash(Eq(3)) == 3)
class Deep(L): pass
print(Deep([1, 2]).total(), Deep.__mro__[1:3])
print(S([1]), S(), FS([2]), FS(), BA(), repr(BA(b"x")), str(S([1])))
class A:
    def __abs__(self): return 7
print(abs(A()), abs(MyInt(-3)), divmod(MyInt(7), MyInt(2)), pow(MyInt(3), 2, MyInt(5)), ord(Name("a")))
''',
              '''[3, 1, 2] 3 6 3 2 [1, 2] L True
[1, 2, 3, 5] True True [1, 2, 3, 5] False True
L [1, 2, 3, 5, 7]
[9, 3, 5, 7] True [9, 3, 5, 7, 1] list [3, 5, 7, 9]
{'a': 1} 1 zzzz 1 True None [('a', 1)] dict
{'a': 1, 'b': 2} {1: 2, 'x': 3}
{'a': 2, 'b': 1, 'c': 1}
21 22 42 int True True 1 21 21.0 True -21    21 21 21
255 0 range(0, 3) 1 5 21 21 (5, 1)
bob 'bob' BOB! bobx 3 b True 1 bob-bob ['b', 'b'] bob|'bob'|  bob bob True str
(1, 2) 1 2 True True (1, 2, 3) P
1 2
1.5 3.5 6.0 2.57 True
[1, 2, 3] 3 True
[1, 2] True
b'ab' ab b'A' 3
BA(b'abc') 3
TypeError type 'bool' is not an acceptable base type
TypeError type 'range' is not an acceptable base type
TypeError multiple bases have instance lay-out conflict
TypeError multiple bases have instance lay-out conflict
TypeError multiple bases have instance lay-out conflict
unhashable type: 'L'
list.__new__(int): int is not a subtype of list
42 item Override! Override! [1, 2] True
True True True
3 (<class '__main__.L'>, <class 'list'>)
S({1}) S() FS({2}) FS() BA(b'') BA(b'x') S({1})
7 3 (3, 1) 4 97
''')

check_program('''class Meta(type):
    def __new__(mcs, name, bases, ns, **kw):
        print("new", mcs.__name__, name, [b.__name__ for b in bases], sorted(k for k in ns if not k.startswith("__")), kw)
        cls = super().__new__(mcs, name, bases, ns)
        cls.tag = name.lower()
        return cls
    def __init__(cls, name, bases, ns, **kw):
        print("init", name, kw)
        super().__init__(name, bases, ns)
    @classmethod
    def __prepare__(mcs, name, bases, **kw):
        print("prepare", name, kw)
        return {"injected": 1}
    def describe(cls): return f"<{cls.__name__}:{cls.tag}>"
class A(metaclass=Meta, flag=True):
    x = 1
    def method(self): return __class__
print(type(A).__name__, A.tag, A.injected, A.describe(), isinstance(A, Meta), isinstance(A, type), A().method() is A)
class B(A):
    y = 2
class Singleton(type):
    instances = {}
    def __call__(cls, *args, **kw):
        if cls not in cls.instances:
            cls.instances[cls] = super().__call__(*args, **kw)
        return cls.instances[cls]
class Conf(metaclass=Singleton):
    def __init__(self, v): self.v = v
print(Conf(1) is Conf(2), Conf(3).v)
class Enumish(type):
    def __iter__(cls): return iter(k for k in vars(cls) if k.isupper())
    def __len__(cls): return sum(1 for _ in cls)
    def __contains__(cls, x): return x in list(cls)
    def __getitem__(cls, k): return getattr(cls, k)
    def __repr__(cls): return f"<enum {cls.__name__}>"
    def __bool__(cls): return False
class Color(metaclass=Enumish):
    RED = 1
    GREEN = 2
class Check(type):
    def __instancecheck__(cls, obj): return obj == 42
    def __subclasscheck__(cls, sub): return sub is int
class Answer(metaclass=Check): pass
print(isinstance(42, Answer), isinstance(1, Answer), issubclass(int, Answer), issubclass(str, Answer), isinstance(Answer(), Answer))
def factory(name, bases, ns):
    return f"made {name} {sorted(k for k in ns if not k.startswith('__'))}"
class F(metaclass=factory):
    z = 3
class M1(type): pass
class M2(type): pass
class P(metaclass=M1): pass
class Q(metaclass=M2): pass
try:
    class R(P, Q): pass
except TypeError as e: print("TypeError", e)
class M3(M1): pass
class S(P, metaclass=M3): pass
class T(S): pass
print(type(T).__name__)
X = Meta("X", (), {"q": 5})
Y = type("Y", (A,), {})
print(type(Y).__name__, Y.tag)
class Attr(type):
    @property
    def area(cls): return "meta-prop"
    shared = "meta-attr"
class W(metaclass=Attr):
    shared = "class-attr"
print(type(Meta), type(type), Meta.__mro__, A.mro())
class Ops(type):
    def __or__(cls, other): return (cls.__name__, other.__name__)
    def __eq__(cls, other): return "eq"
    __hash__ = type.__hash__ if hasattr(type, "__hash__") else None
class O1(metaclass=Ops): pass
class O2(metaclass=Ops): pass
class Sub(metaclass=Meta, extra=9):
    pass
class Init(type):
    def __init_subclass__(cls, **kw): print("meta subclass", cls.__name__)
class Init2(Init): pass
class Base:
    def __init_subclass__(cls, **kw):
        print("init_subclass", cls.__name__, kw)
class Child(Base, metaclass=M1, k=1): pass
''',
              '''prepare A {'flag': True}
new Meta A [] ['injected', 'method', 'x'] {'flag': True}
init A {'flag': True}
Meta a 1 <A:a> True True True
prepare B {}
new Meta B ['A'] ['injected', 'y'] {}
init B {}
True 1
True False True False True
TypeError metaclass conflict: the metaclass of a derived class must be a (non-strict) subclass of the metaclasses of all its bases
M3
new Meta X [] ['q'] {}
init X {}
new Meta Y ['A'] [] {}
init Y {}
Meta y
<class 'type'> <class 'type'> (<class '__main__.Meta'>, <class 'type'>, <class 'object'>) [<class '__main__.A'>, <class 'object'>]
prepare Sub {'extra': 9}
new Meta Sub [] ['injected'] {'extra': 9}
init Sub {'extra': 9}
meta subclass Init2
init_subclass Child {'k': 1}
''')

check_program('''print(list[int], dict[str, list[int]], tuple[int, ...], tuple[()], type[int], set[bytes], frozenset[int])
print(list[int] == list[int], list[int] == list, hash(list[int]) == hash(list[int]))
print(list[int](), list[int]((1, 2)), list[int].__origin__, list[int].__args__, list[int].__parameters__)
print(list[int].__mro_entries__((list[int],)), list[int].__class__, list[int].__module__)
print(list[[int, str]], list[1, "a"], list[None], list[...])
def f(): pass
print(list[f])
try: list[int][int]
except TypeError as e: print(e)
try: isinstance([], list[int])
except TypeError as e: print(e)
try: issubclass(list, list[int])
except TypeError as e: print(e)
class L(list[int]): pass
print(L.__mro__, L.__orig_bases__, L[str])
print(BaseExceptionGroup[int], ExceptionGroup[int], classmethod[int])
x = list[int]
try: x.foo = 1
except AttributeError as e: print(e)
try: int[str]
except TypeError as e: print(e)
print(isinstance(1, (str, (int,))), isinstance(1, (str,)))
try: isinstance(1, 1)
except TypeError as e: print(e)
try: issubclass(int, 1)
except TypeError as e: print(e)
''',
              '''list[int] dict[str, list[int]] tuple[int, ...] tuple[()] type[int] set[bytes] frozenset[int]
True False True
[] [1, 2] <class 'list'> (<class 'int'>,) ()
(<class 'list'>,) <class 'types.GenericAlias'> builtins
list[[int, str]] list[1, 'a'] list[None] list[...]
list[__main__.f]
list[int] is not a generic class
isinstance() argument 2 cannot be a parameterized generic
issubclass() argument 2 cannot be a parameterized generic
(<class '__main__.L'>, <class 'list'>, <class 'object'>) (list[int],) __main__.L[str]
BaseExceptionGroup[int] ExceptionGroup[int] classmethod[int]
'types.GenericAlias' object has no attribute 'foo' and no __dict__ for setting new attributes
type 'int' is not subscriptable
True False
isinstance() arg 2 must be a type, a tuple of types, or a union
issubclass() arg 2 must be a class, a tuple of classes, or a union
''')

check_program('''print(int | str, int | None, None | int, int | int, int | str | int, type(int | str))
print((int | str) == (str | int), hash(int | str) == hash(str | int), (int | str).__args__, (int | None).__args__)
print(int | list[int], list[int] | None, str | list[int] | None, (int | list[int]).__args__)
print(isinstance(1, int | str), isinstance("a", int | str), isinstance(1.0, int | str), issubclass(bool, int | None))
print(isinstance(1, int | list[int]))
try: isinstance([], int | list[int])
except TypeError as e: print(e)
try: int | 1
except TypeError as e: print(e)
U = type(int | str)
print(U, U.__name__, U.__module__, U[int, str], U[int])
try: U()
except TypeError as e: print(e)
try: U[()]
except TypeError as e: print(e)
class M(type):
    def __or__(cls, other): return "meta"
class A(metaclass=M): pass
print(A | int, int | A if False else 0)
x = int | str
d = {x: 1}
print(d[str | int])
print(repr(int | None | str), (int | str) | (bytes | None))
''',
              '''int | str int | None None | int <class 'int'> int | str <class 'typing.Union'>
True True (<class 'int'>, <class 'str'>) (<class 'int'>, <class 'NoneType'>)
int | list[int] list[int] | None str | list[int] | None (<class 'int'>, list[int])
True True False True
True
isinstance() argument 2 cannot be a parameterized generic
unsupported operand type(s) for |: 'type' and 'int'
<class 'typing.Union'> Union typing int | str <class 'int'>
cannot create 'typing.Union' instances
Cannot take a Union of no types.
meta 0
1
int | None | str int | str | bytes | None
''')

check_program('''def f[T: int, *Ts, **P, U: (int, str) = str](): pass
T, Ts, P, U = f.__type_params__
print(repr(T), T.__name__, T.__bound__, T.__constraints__, T.__default__, T.has_default(), T.__infer_variance__, T.__covariant__, T.__module__)
print(repr(U), U.__bound__, U.__constraints__, U.__default__, U.has_default())
print(repr(Ts), Ts.__default__, repr(P), P.args, P.kwargs, P.__bound__)
print(T | None, list[T], list[T][int], dict[T, U][int, str])
try: list[T][int, str]
except TypeError as e: print(e)
type A[K] = dict[K, int]
print(A, type(A).__name__, A.__name__, A.__value__, A.__type_params__, A[str], type(A[str]), A.__module__, A[str].__origin__ is A)
type B = int
print(B.__value__, B.__type_params__, B | None)
try: B()
except TypeError as e: print(e)
class C[T]:
    def m(self) -> T: ...
print(C.__type_params__, C.__parameters__, C[int], C.__mro__, C.__orig_bases__, C.m.__annotations__)
print(f.__name__, f.__qualname__, type(T).__module__, type(T).__name__, C.__qualname__, C.m.__qualname__)
print(T.evaluate_bound(1), U.evaluate_constraints(1), U.evaluate_default(1), T.evaluate_bound.__name__)
try: U.evaluate_default(3)
except NotImplementedError: print("NIE")
class D(C[int]): pass
print(D.__mro__, D.__orig_bases__, D.__parameters__)
class Outer:
    x = int
    def g[V: x](self, a: x) -> V: return V
    type Al = x
print(Outer.g.__type_params__[0].__bound__, Outer.g.__annotations__, Outer.Al.__value__, Outer.g.__qualname__)
def deco(fn): fn.decorated = True; return fn
@deco
def h[X](a=1, *, b=2) -> X: return a, b, X
print(h(), h.decorated, h.__defaults__, h.__kwdefaults__, h.__annotations__)
def outer():
    y = 5
    def inner[Z](): return y, Z
    return inner()
print(outer())
class Sup:
    def m(self): return "sup"
class Sub[T](Sup):
    def m(self): return super().m() + "!"
print(Sub().m(), Sub.__mro__, Sub.__bases__)
type Rec = list[Rec] | int
print(Rec.__value__)
def g2[*Ts2](*args: *Ts2): pass
print(g2.__annotations__)
class G[*Ts3, T3]: pass
print(G[int, str, bytes], G.__parameters__, G.__orig_bases__)
''',
              '''T T <class 'int'> () typing.NoDefault False True False typing
U None (<class 'int'>, <class 'str'>) <class 'str'> True
Ts typing.NoDefault P P.args P.kwargs None
T | None list[T] list[int] dict[int, str]
Too many arguments for list[T]; actual 2, expected 1
A TypeAliasType A dict[K, int] (K,) __main__.A[str] <class 'types.GenericAlias'> __main__ True
<class 'int'> () __main__.B | None
'typing.TypeAliasType' object is not callable
(T,) (T,) __main__.C[int] (<class '__main__.C'>, <class 'typing.Generic'>, <class 'object'>) (typing.Generic[T],) {'return': T}
f f typing TypeVar C C.m
<class 'int'> (<class 'int'>, <class 'str'>) <class 'str'> T
NIE
(<class '__main__.D'>, <class '__main__.C'>, <class 'typing.Generic'>, <class 'object'>) (__main__.C[int],) ()
<class 'int'> {'a': <class 'int'>, 'return': V} <class 'int'> Outer.g
(1, 2, X) True (1,) {'b': 2} {'return': X}
(5, Z)
sup! (<class '__main__.Sub'>, <class '__main__.Sup'>, <class 'typing.Generic'>, <class 'object'>) (<class '__main__.Sup'>, <class 'typing.Generic'>)
list[__main__.Rec] | int
{'args': typing.Unpack[Ts2]}
__main__.G[int, str, bytes] (Ts3, T3) (typing.Generic[typing.Unpack[Ts3], T3],)
''')

check_program('for s in ["1_0.5", "1__0", "_1.0", "1.0_", "0x1p3", "  inf ", "-Infinity", "nAn", "1e5", "1e_5", ".5", "5.", "1_0e1_0", "\u2003 1.5\u2003", "+.e1", "", " ", "1e", "e1", "-.5e-3", "1.5j", "١.٥", "infinit", "+nan", "1\\x00", "١٢"]:\n    try: print(repr(s), float(s))\n    except ValueError as e: print(e)\nfor s, b in [("12a", 10), (" 1 2", 10), ("١x", 10), ("", 10), ("0x1g", 0), ("z", 16), ("١_٢", 10), ("\u2003 7 \u2003", 10), ("１２", 16), ("x" * 300, 10), ("0b101", 0), ("1_000", 10)]:\n    try: print(repr(s)[:20], int(s, b))\n    except ValueError as e: print(e)\ntry: int(b"z")\nexcept ValueError as e: print(e)\nprint(complex("١+2j"), complex(" (1+2j) "), float(b"1.5"), int(b" 12 "))\n',
              "'1_0.5' 10.5\ncould not convert string to float: '1__0'\ncould not convert string to float: '_1.0'\ncould not convert string to float: '1.0_'\ncould not convert string to float: '0x1p3'\n'  inf ' inf\n'-Infinity' -inf\n'nAn' nan\n'1e5' 100000.0\ncould not convert string to float: '1e_5'\n'.5' 0.5\n'5.' 5.0\n'1_0e1_0' 100000000000.0\n'\\u2003 1.5\\u2003' 1.5\ncould not convert string to float: '+.e1'\ncould not convert string to float: ''\ncould not convert string to float: ' '\ncould not convert string to float: '1e'\ncould not convert string to float: 'e1'\n'-.5e-3' -0.0005\ncould not convert string to float: '1.5j'\n'١.٥' 1.5\ncould not convert string to float: 'infinit'\n'+nan' nan\ncould not convert string to float: '1\\x00'\n'١٢' 12.0\ninvalid literal for int() with base 10: '12a'\ninvalid literal for int() with base 10: ' 1 2'\ninvalid literal for int() with base 10: '١x'\ninvalid literal for int() with base 10: ''\ninvalid literal for int() with base 0: '0x1g'\ninvalid literal for int() with base 16: 'z'\n'١_٢' 12\n'\\u2003 7 \\u2003' 7\n'１２' 18\ninvalid literal for int() with base 10: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n'0b101' 5\n'1_000' 1000\ninvalid literal for int() with base 10: b'z'\n(1+2j) (1+2j) 1.5 12\n")

check_program('''def clean(s):
    out = ""; i = 0
    while i < len(s):
        if s.startswith("0x", i):
            i += 2
            while i < len(s) and s[i] in "0123456789abcdef": i += 1
            out += "ADDR"
        else:
            out += s[i]; i += 1
    return out
def f(): pass
class A:
    def m(self): pass
    def __repr__(self): return "A!" + super().__repr__()[:3]
    def __eq__(self, o): return super().__eq__(o)
    def __str__(self): return object.__str__(self)
a = A()
for x in [f, A.m, a.m, print, len, [].append, list.append, int.__add__, (1).__add__, str.upper, "x".upper, dict.fromkeys, object.__init__, object.__repr__, a]:
    print(clean(repr(x)))
print(print.__name__, len.__qualname__, list.append.__qualname__, [].append.__qualname__, [].append.__self__, str.upper.__name__, list.append.__objclass__)
print(a == a, a == 1, a != a, str(a), clean(object.__repr__(a)), object.__format__(a, ""))
class L(list):
    def __repr__(self): return "L" + super().__repr__()
    def append(self, x): super().append(x * 2)
l = L([1]); l.append(2); print(l, list.__len__(l), list.__getitem__(l, 1))
class I(int):
    def __add__(self, o): return int.__add__(self, o) + 100
print(I(1) + 2, int.__add__(1, 2.5), float.__add__(1.5, 1), int.__eq__(1, 1.0), float.__eq__(1.0, 1), (1).__eq__("a"))
print(int.__lt__(1, 2), str.__lt__("a", "b"), list.__eq__([1], [1]), set.__eq__({1}, frozenset({1})), (5).__truediv__(2), (5).__rsub__(10))
print(int.__pow__(2, 10), int.__pow__(2, 10, 7), divmod(7, 2), int.__divmod__(7, 2), int.__rdivmod__(2, 7), float.__floor__(2.5), float.__ceil__(2.5), int.__index__(5), int.__bool__(0), float.__trunc__(-2.7))
d = {}; dict.__setitem__(d, 1, 2); print(d, dict.__getitem__(d, 1), dict.__contains__(d, 1), dict.__len__(d)); dict.__delitem__(d, 1); print(d)
x = [1]; print(list.__iadd__(x, [2]) is x, x, list.__mul__([1], 2), list.__rmul__([1], 2), str.__mod__("%s!", 3))
try: list.append(1, 2)
except TypeError as e: print(e)
try: list.append()
except TypeError as e: print(e)
print(sorted(["b", "A"], key=str.lower), list(map(str.strip, [" a "])), str.join(",", "ab"), int.bit_length(255), bool.__and__(True, False), bool.__repr__(True), int.__repr__(True))
print(int.__format__(5, "03"), str.__format__("a", ">3"), object.__format__(1, ""), int.__hash__(5) == hash(5), complex.__abs__(3+4j), int.__neg__(5), float.__pos__(-1.0))
try: object.__format__(a, "x")
except TypeError as e: print(e)
s = {1}; print(set.__ior__(s, {2}) is s, s, set.__isub__(s, {1}), set.__iand__(s, {2, 3}), set.__ixor__(s, {5}), s)
d = {1: 2}; print(dict.__ior__(d, {3: 4}) is d, d, set.__ior__(s, [1]))
b = bytearray(b"a"); print(bytearray.__iadd__(b, b"b") is b, b, list.__imul__([1, 2], 2))
''',
              '''<function f at ADDR>
<function A.m at ADDR>
<bound method A.m of A!<__>
<function run_program.<locals>.print_ at ADDR>
<built-in function len>
<built-in method append of list object at ADDR>
<method 'append' of 'list' objects>
<slot wrapper '__add__' of 'int' objects>
<method-wrapper '__add__' of int object at ADDR>
<method 'upper' of 'str' objects>
<built-in method upper of str object at ADDR>
<built-in method fromkeys of type object at ADDR>
<slot wrapper '__init__'>
<slot wrapper '__repr__'>
A!<__
print_ len list.append list.append [] upper <class 'list'>
True False False A!<__ <__main__.A object at ADDR> A!<__
L[1, 4] 2 4
103 NotImplemented 2.5 NotImplemented True NotImplemented
True True True True 2.5 5
1024 2 (3, 1) (3, 1) (3, 1) 2 3 5 False -2
{1: 2} 2 True 1
{}
True [1, 2] [1, 1] [1, 1] 3!
descriptor 'append' for 'list' objects doesn't apply to a 'int' object
unbound method list.append() needs an argument
['A', 'b'] ['a'] a,b 8 False True 1
005   a 1 True 5.0 -5 -1.0
unsupported format string passed to A.__format__
True {2, 5} {2, 5} {2, 5} {2, 5} {2, 5}
True {1: 2, 3: 4} NotImplemented
True bytearray(b'ab') [1, 2, 1, 2]
''')

check_program('''d = {'eggs': 2, 'sausage': 1, 'bacon': 1, 'spam': 500}
keys, values, items = d.keys(), d.values(), d.items()
print(keys, values, items, type(keys), type(values).__name__, type(items))
print(len(keys), list(keys), list(values), sorted(items), bool({}.keys()), bool(keys))
del d['eggs']; del d['sausage']
print(list(keys), list(values), items, len(items))
print(sorted(keys & {'juice', 'spam', 'bacon'}), sorted(keys ^ {'sausage', 'juice'}), keys - {'spam'}, sorted(keys | ['x']))
print(['spam', 1] & keys, sorted({'spam'} | keys), ('bacon',) - keys, 'spam' in keys, 'x' in keys, 500 in values, ('spam', 500) in items, ('spam', 1) in items, ['spam', 500] in items)
print(keys == {'bacon', 'spam'}, {'bacon', 'spam'} == keys, keys == ['bacon', 'spam'], keys != {'bacon'}, keys < {'bacon', 'spam', 1}, keys <= keys, keys > {'spam'}, keys >= frozenset())
print(items == {('bacon', 1), ('spam', 500)}, items == d.items(), values == values, values == d.values(), d.keys() == {'bacon': 9}.keys())
print(list(reversed(keys)), list(reversed(values)), list(reversed(items)), list(reversed(d)))
print(keys.isdisjoint({'x'}), keys.isdisjoint(['spam']), items.isdisjoint([('spam', 500)]))
m = keys.mapping; print(m, m['spam'], len(m), type(m), m == d, list(m), 'spam' in m, m.get('q', 0), type(m).__name__)
try: hash(keys)
except TypeError as e: print(e)
try: hash(items)
except TypeError as e: print(e)
print(type(hash(values)))
try: values.isdisjoint
except AttributeError as e: print(e)
try: keys < [1]
except TypeError as e: print(e)
try: values & {1}
except TypeError as e: print(e)
try:
    for k in keys: d['new'] = 1
except RuntimeError as e: print(e)
try:
    for k in reversed(keys): d['new2'] = 1
except RuntimeError as e: print(e)
e = {}; e[1] = e.keys(); e[2] = e.values(); print(e)
print(dict.keys(d), dict.__len__(keys) if False else len(d.items()), list(zip(d.values(), d.keys())))
print(sorted(set(d.items())), tuple(d), {**dict(d.items())}, max(d.values()), sum(d.values()))
class D(dict): pass
dd = D(a=1); kv = dd.keys(); dd['b'] = 2; print(kv, type(kv).__name__)
print(sorted({1: 'a', 2: 'b'}.items() - {(1, 'a')}), {1: [1]}.items() == {1: [1]}.items(), {1: 2}.items() & {(1, 2)}, {1: 2}.items() | {1: 3}.items())
print(dict_keys := type({}.keys()), isinstance(keys, type({}.keys())))
try: type({}.keys())()
except TypeError as e: print(e)
''',
              '''dict_keys(['eggs', 'sausage', 'bacon', 'spam']) dict_values([2, 1, 1, 500]) dict_items([('eggs', 2), ('sausage', 1), ('bacon', 1), ('spam', 500)]) <class 'dict_keys'> dict_values <class 'dict_items'>
4 ['eggs', 'sausage', 'bacon', 'spam'] [2, 1, 1, 500] [('bacon', 1), ('eggs', 2), ('sausage', 1), ('spam', 500)] False True
['bacon', 'spam'] [1, 500] dict_items([('bacon', 1), ('spam', 500)]) 2
['bacon', 'spam'] ['bacon', 'juice', 'sausage', 'spam'] {'bacon'} ['bacon', 'spam', 'x']
{'spam'} ['bacon', 'spam'] set() True False True True False False
True True False True True True True True
True True True False False
['spam', 'bacon'] [500, 1] [('spam', 500), ('bacon', 1)] ['spam', 'bacon']
True False False
{'bacon': 1, 'spam': 500} 500 2 <class 'mappingproxy'> True ['bacon', 'spam'] True 0 mappingproxy
unhashable type: 'dict_keys'
unhashable type: 'dict_items'
<class 'int'>
'dict_values' object has no attribute 'isdisjoint'
'<' not supported between instances of 'dict_keys' and 'list'
unsupported operand type(s) for &: 'dict_values' and 'set'
dictionary changed size during iteration
dictionary changed size during iteration
{1: dict_keys([1, 2]), 2: dict_values([dict_keys([1, 2]), ...])}
dict_keys(['bacon', 'spam', 'new', 'new2']) 4 [(1, 'bacon'), (500, 'spam'), (1, 'new'), (1, 'new2')]
[('bacon', 1), ('new', 1), ('new2', 1), ('spam', 500)] ('bacon', 'spam', 'new', 'new2') {'bacon': 1, 'spam': 500, 'new': 1, 'new2': 1} 500 503
dict_keys(['a', 'b']) dict_keys
[(2, 'b')] True {(1, 2)} {(1, 2), (1, 3)}
<class 'dict_keys'> True
cannot create 'dict_keys' instances
''')
