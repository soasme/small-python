# spec: PLS-315 27.2
# description: Programs on generators, each with the output CPython 3.15 gives.
from harness import *

check_program('''items = [0, 1, 2]
print(items.insert(-200, -1), items.insert(200, 3), items)
print(items.extend(items), items)
copy = items.copy()
print(copy is items, copy == items, copy.reverse(), copy)
print(items.remove(1), items.pop(), items)
print(items.count(2), items.index(2), items.index(2, -3, 10**100))
print(tuple(items).count(2), tuple(items).index(2, -3, 10**100))
class Index:
    def __index__(self): return 1
print(items.pop(Index()))
print(items.clear(), items, copy)
nan = float('nan')
print([nan].count(nan), (nan,).index(nan))
def fail():
    yield 5
    raise ValueError('iteration')
try: items.extend(fail())
except ValueError as error: print(error, items)
''',
              '''None None [-1, 0, 1, 2, 3]
None [-1, 0, 1, 2, 3, -1, 0, 1, 2, 3]
False True None [3, 2, 1, 0, -1, 3, 2, 1, 0, -1]
None 3 [-1, 0, 2, 3, -1, 0, 1, 2]
2 2 7
2 7
0
None [] [3, 2, 1, 0, -1, 3, 2, 1, 0, -1]
1 0
iteration [5]
''')

check_program('''x: int = 1
if x:
    y: str
z: "q"
print(__annotate__(1), __annotate__.__name__, __annotate__.__qualname__)
try: __annotate__(3)
except NotImplementedError as e: print("NIE", repr(e))
class A:
    a: int
    if True: b: str = "x"
    def f(self, p: b, *q: "s", r: int = 2, **k: b) -> A: pass
print(A.__annotations__, A.__annotate__.__qualname__, A.f.__annotations__)
def g(): pass
print(g.__annotate__, g.__annotations__)
def h():
    w: int = 1
    return w
print(h.__annotate__, h())
class B: pass
print(B.__annotations__, "__annotations__" in B.__dict__, B.__annotate__)
class C:
    x: undefined
try: C.__annotations__
except NameError as e: print(e)
print(C.__annotate__.__code__.co_varnames)
class D:
    __p: int
print(D.__annotations__)
o = A(); o.attr: int = 5; print(o.attr)
d = {}; d["k"]: int = 3; print(d)
def gen():
    v: int = yield 1
    print("got", v)
gg = gen(); next(gg)
try: gg.send(9)
except StopIteration: pass
lam = lambda a: a
print(lam(3))
''',
              '''{'x': <class 'int'>, 'y': <class 'str'>, 'z': 'q'} __annotate__ __annotate__
NIE NotImplementedError()
{'a': <class 'int'>, 'b': <class 'str'>} A.__annotate__ {'p': 'x', 'q': 's', 'r': <class 'int'>, 'k': 'x', 'return': <class '__main__.A'>}
None {}
None 1
{} False None
name 'undefined' is not defined
('format',)
{'_D__p': <class 'int'>}
5
{'k': 3}
got 9
3
''')

check_program('''class V:
    def __bool__(s): raise TypeError("no bool")
    def __lt__(s, o): return V()
try: V() < 1 < 2
except TypeError as e: print(e)
def g():
    try: yield V() < 1 < 2
    except TypeError as e: yield str(e)
print(list(g()), 1 < 2 < 3, 1 < 3 < 2)
''',
              '''no bool
['no bool'] True False
''')

check_program('''def g(n):
    print('start')
    for i in range(n):
        x = yield i
        print('sent', x)
    return 42
a = g(2)
try:
    a.send(3)
except TypeError:
    print('unstarted')
print(next(a), a.send(7))
try:
    next(a)
except StopIteration as e:
    print(e.value, e.args)
print(next(a, 'done'), a.close())
''',
              '''unstarted
start
sent 7
0 1
sent None
42 (42,)
done None
''')

check_program('''def sub():
    x = yield 1
    yield x
    return 8
def g():
    result = yield from sub()
    yield result
    yield from [4, 5]
a = g()
print(next(a), a.send(9), list(a))
f = lambda: (yield from sub())
a = f()
print(next(a), a.send(6))
try:
    next(a)
except StopIteration as e:
    print(e.value)
''',
              '''1 9 [8, 4, 5]
1 6
8
''')

check_program('''def g():
    try:
        yield 1
    except ValueError as e:
        yield e.args
        try:
            raise
        except ValueError:
            yield 2
    finally:
        yield 3
    try:
        print(e)
    except UnboundLocalError:
        yield 4
a = g()
print(next(a), a.throw(ValueError('x')), list(a))
''',
              '''1 ('x',) [2, 3, 4]
''')

check_program('''def g():
    for i in range(4):
        try:
            yield i
            if i == 0:
                continue
            break
        finally:
            yield i + 10
    else:
        yield 99
    try:
        return 42
    finally:
        yield 50
a = g()
print([next(a) for i in range(5)])
try:
    next(a)
except StopIteration as e:
    print(e.value)
''',
              '''[0, 10, 1, 11, 50]
42
''')

check_program('''def g():
    try:
        yield 1
    finally:
        print('closed')
        return 42
a = g()
print(next(a), a.close(), a.close())
def bad():
    try:
        yield 1
    finally:
        yield 2
a = bad()
print(next(a))
try:
    a.close()
except RuntimeError as e:
    print(e)
print(a.close())
''',
              '''closed
1 42 None
1
generator ignored GeneratorExit
None
''')

check_program('''class C:
    def __init__(self, name): self.name = name
    def __enter__(self): print('enter', self.name); return self
    def __exit__(self, t, v, tb): print('exit', self.name, t is ValueError); return t is ValueError
def g():
    with C('outer'), C('inner') as c:
        yield c.name
        raise ValueError('stop')
    yield 2
a = g()
print(next(a), list(a))
a = g()
print(next(a), a.close())
''',
              '''enter outer
enter inner
exit inner True
exit outer False
inner [2]
enter outer
enter inner
exit inner False
exit outer False
inner None
''')

check_program('''def mark(x): print('mark', x); return x
def call(*args, **kw): print(args, kw); return 99
def g():
    x = mark(1) + (yield mark(2)) * mark(3)
    yield x
    yield call(mark(4), (yield 5), named=(yield 6))
    yield [mark(7), (yield 8), *(yield 9)]
    yield {(yield 10): (yield 11), **(yield 12)}
    yield (yield 13) < (yield 14) < (yield 15)
    yield (yield 16) and (yield 17)
a = g()
print(next(a), a.send(10), next(a), a.send(20), a.send(30))
print(next(a), a.send(80), a.send([90]))
print(next(a), a.send('x'), a.send(110), a.send({'y': 120}))
print(next(a), a.send(1), a.send(2), a.send(3))
print(next(a), a.send(0), list(a))
''',
              '''mark 1
mark 2
mark 3
mark 4
(4, 20) {'named': 30}
2 31 5 6 99
mark 7
8 9 [7, 80, 90]
10 11 12 {'x': 110, 'y': 120}
13 14 15 True
16 0 []
''')

check_program('''def g():
    try:
        yield 1
    except ValueError:
        try:
            yield 2
        finally:
            try:
                raise
            except ValueError:
                yield 3
    yield 4
a = g()
print(next(a), a.throw(ValueError), next(a), next(a), list(a))
def stop():
    yield 1
    raise StopIteration('oops')
a = stop()
print(next(a))
try:
    next(a)
except RuntimeError as e:
    print(e, e.__cause__.value)
''',
              '''1 2 3 4 []
1
generator raised StopIteration oops
''')

check_program('''def g():
    while True:
        try:
            raise
        except BaseException as e:
            yield type(e).__name__
a = g()
print(next(a))
try:
    raise ValueError
except ValueError:
    print(next(a))
print(next(a))
def rethrow(): raise
def h():
    try:
        yield 1
        rethrow()
    finally:
        print('finally')
a = h()
print(next(a))
try:
    raise KeyError
except KeyError:
    try:
        next(a)
    except KeyError:
        print('inherited')
''',
              '''RuntimeError
ValueError
RuntimeError
1
finally
inherited
''')

check_program('''def g(d):
    d[(yield 'target')] += (yield 'rhs')
    d[(yield 'a')] = d[(yield 'b')] = 27
    f = lambda x=(yield 'default'): x
    yield f()
    def inner(x=(yield 'def')): return x
    yield inner()
    yield list(i for i in [(yield 'iterable')])
data = [1, 2]
a = g(data)
print(next(a), a.send(0), a.send(10), data)
print(a.send(0), data, a.send(1), data)
print(a.send(42), next(a), a.send(43), next(a), a.send(44), list(a))
''',
              '''target rhs a [11, 2]
b [27, 27] default [27, 27]
42 def 43 iterable [44] []
''')

check_program('''def g():
    try:
        yield 'start'
    except ValueError as e:
        yield e.args
    finally:
        print('inner finally')
    return 'returned'
def outer():
    try:
        yield (yield from g())
    finally:
        print('outer finally')
a = outer()
print(next(a), a.throw(ValueError('handled')), next(a), list(a))
a = outer()
print(next(a), a.close())
class I:
    def __iter__(self): return self
    def __next__(self): return 1
    def send(self, value): return value
    def throw(self, exc): print(type(exc).__name__); raise StopIteration(42)
    def close(self): print('iterator close')
def delegate(): yield (yield from I())
a = delegate()
print(next(a), a.send(2), a.throw(KeyError), list(a))
a = delegate()
print(next(a), a.close())
''',
              '''inner finally
outer finally
start ('handled',) returned []
inner finally
outer finally
start None
type
1 2 42 []
iterator close
1 None
''')

check_program('''a = [0,1,2,3,4]
def replacement():
    a[:] = [10,11]
    yield 9
a[1:4] = replacement()
print(a)
def g():
    yield [0,1,2,3,4][(yield 1):(yield 2):(yield 3)]
a = g()
print(next(a), a.send(0), a.send(5), a.send(2), list(a))
''',
              '''[10, 9]
1 2 3 [0, 2, 4] []
''')

check_program('''def g(data):
    data[(yield 1)], *data[(yield 2)], data[(yield 3)] = [10, 20, 30, 40]
    for data[(yield 4)] in [50, 60]:
        yield data
    assert (yield 5), (yield 6)
data = [0,0,0]
a = g(data)
print(next(a), a.send(0), data, a.send(1), data, a.send(2), data)
print(a.send(0), next(a), a.send(2), next(a), a.send(False))
try:
    a.send('failed')
except AssertionError as e:
    print(e)
class C:
    def __enter__(self): return [10, 20]
    def __exit__(self, t, e, tb): print('exit', t is ValueError)
def h(data):
    with C() as (data[(yield 'index')], data[1]):
        yield data
a = h(data)
print(next(a), a.send(0), list(a))
a = h(data)
print(next(a))
try:
    a.throw(ValueError)
except ValueError:
    print('caught')
''',
              '''1 2 [10, [20, 30], 40] 3 [10, [20, 30], 40] 4 [10, [20, 30], 40]
[50, [20, 30], 60] 4 [50, [20, 30], 60] 5 6
failed
exit False
index [10, 20, 60] []
index
exit True
caught
''')

check_program('''def outer(x):
    class C:
        nonlocal x
        x += 1
        def inc(self):
            nonlocal x
            x += 1
            return x
        def values(self):
            nonlocal x
            for i in range(2):
                x += 1
                yield x
    return C()
a = outer(10)
print(a.inc(), list(a.values()), a.inc(), hasattr(type(a), 'x'))
x = 3
class C:
    x = 4
    values = [x for i in range(2)]
print(C.values)
''',
              '''12 [13, 14] 15 False
[3, 3]
''')

check_program('''x = 1
def global_except():
    global x
    try:
        raise ValueError(3)
    except ValueError as x:
        print(x)
global_except()
print('exists', 'x' in {'a': 1})
try:
    print(x)
except NameError:
    print('exception binding cleared')
def outer():
    x = 5
    def gen():
        nonlocal x
        try:
            raise ValueError(6)
        except ValueError as x:
            yield x.args
        yield 7
    g = gen()
    print(next(g), x.args, next(g))
    try:
        print(x)
    except UnboundLocalError:
        print('nonlocal exception cleared')
outer()
''',
              '''3
exists False
exception binding cleared
(6,) (6,) 7
nonlocal exception cleared
''')

check_program('''events = []
def decorate(fn):
    events.append(fn.__name__)
    return fn
def g():
    @decorate
    def f(x=(yield 'default')):
        return x
    yield f()
    @decorate
    class C:
        value = 4
    yield C.value
it = g()
print(next(it), events)
print(it.send(12), events)
print(next(it), events)
''',
              '''default []
12 ['f']
4 ['f', 'C']
''')

check_program('''def g():
    @(yield 'decorator')
    def f(x=3):
        return x
    yield f()
it = g()
print(next(it))
print(it.send(lambda f: f))
''',
              '''decorator
3
''')
