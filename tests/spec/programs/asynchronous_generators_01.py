# spec: PLS-315 27.5
# description: Programs on asynchronous generators, each with the output CPython 3.15 gives.
from harness import *

check_program('''def factory():
    def function(a, /, *, b=1):
        yield a + b
    return function
f, other = factory(), factory()
g = f(2)
print(f.__code__ is other.__code__, g.gi_code is f.__code__)
code = g.gi_code
print(code.co_name, code.co_argcount, code.co_posonlyargcount, code.co_kwonlyargcount)
print(next(g))
g.close()
print(g.gi_code is code, g.gi_frame)
f = other = None
print(g.gi_code.co_name)
async def coroutine(): return 1
c = coroutine()
print(c.cr_code is coroutine.__code__)
c.close()
print(c.cr_code.co_name, c.cr_frame)
async def asynchronous(): yield 1
a = asynchronous()
print(a.ag_code is asynchronous.__code__)
try: a.aclose().send(None)
except StopIteration: pass
print(a.ag_code.co_name, a.ag_frame)
def expression(): return (x for x in [])
g, h = expression(), expression()
print(g.gi_code is h.gi_code, g.gi_code.co_name, g.gi_code.co_argcount)
g.close()
h.close()
print(g.gi_code is h.gi_code)
''',
              '''True True
function 1 1 1
3
True None
function
True
coroutine None
True
asynchronous None
True <genexpr> 1
True
''')

check_program('''for cause in [None, KeyError, KeyError('cause')]:
    try:
        try: raise TypeError('context')
        except TypeError: raise ValueError('raised') from cause
    except ValueError as error:
        print(type(error.__context__).__name__, type(error.__cause__).__name__, error.__suppress_context__)
        error.__suppress_context__ = False
        try: raise error
        except ValueError as again: print(again is error, again.__suppress_context__)
calls = []
class Raised(Exception):
    def __init__(self): calls.append('raised')
class Cause(Exception):
    def __init__(self): calls.append('cause')
def value(): calls.append('value'); return Raised
def cause(): calls.append('cause expression'); return Cause
try: raise value() from cause()
except Raised as error: print(calls, type(error.__cause__).__name__)
class Other:
    def __init__(self): calls.append('invalid constructor')
for value in [Other, Other(), 42]:
    calls = []
    try: raise value
    except TypeError: print('invalid exception', calls)
    try: raise ValueError from value
    except TypeError: print('invalid cause', calls)
class Broken(Exception):
    def __init__(self): raise RuntimeError('constructor')
try: raise ValueError from Broken
except RuntimeError as error: print(error)
error = ValueError()
print(error.__cause__, error.__suppress_context__)
error.__cause__ = None
print(error.__cause__, error.__suppress_context__)
for name, value in [('__cause__', KeyError), ('__context__', 1), ('__suppress_context__', 1), ('__traceback__', 1)]:
    try: setattr(error, name, value)
    except TypeError: print('invalid attribute', name)
try: del error.__cause__
except TypeError: print('cannot delete cause')
def suspended():
    try:
        raise (yield 'exception') from (yield 'cause')
    except ValueError as error:
        yield type(error.__cause__).__name__, error.__suppress_context__
g = suspended()
print(next(g), g.send(ValueError), g.send(KeyError), next(g, 'done'))
class Await:
    def __await__(self):
        result = yield 'await'
        return result
async def raised():
    try: raise await Await() from await Await()
    except ValueError as error: return error.__cause__, error.__suppress_context__
g = raised()
print(g.send(None), g.send(ValueError))
try: g.send(None)
except StopIteration as end: print(end.value)
for message in [(3,), None, [], {'value': 4}]:
    try: assert False, message
    except AssertionError as error: print(error.args[0] is message, error.args)
try: assert False
except AssertionError as error: print(error.args)
class BadTruth:
    def __bool__(self): raise ValueError('truth')
def wrong(): print('message must not run')
try: assert BadTruth(), wrong()
except ValueError as error: print(error)
def check():
    try: assert (yield 'test'), (yield 'message')
    except AssertionError as error: yield error.args
g = check()
print(next(g), g.send(False), g.send((3,)), next(g, 'done'))
''',
              '''TypeError NoneType True
True False
TypeError KeyError True
True False
TypeError KeyError True
True False
['value', 'cause expression', 'raised', 'cause'] Cause
invalid exception []
invalid cause []
invalid exception []
invalid cause []
invalid exception []
invalid cause []
constructor
None False
None True
invalid attribute __cause__
invalid attribute __context__
invalid attribute __suppress_context__
invalid attribute __traceback__
cannot delete cause
exception cause ('KeyError', True) done
await await
(None, True)
True ((3,),)
True (None,)
True ([],)
True ({'value': 4},)
()
truth
test message ((3,),) done
''')

check_program('''class Pause:
    def __init__(self, value): self.value = value
    def __await__(self):
        yield 'pause'
        return self.value
async def values():
    for i in range(4):
        await Pause(None)
        yield i
async def run():
    x = 99
    result = [await Pause(x * 2) async for x in values() if await Pause(x % 2)]
    print(result, x)
    print({x: await Pause(x + 1) async for x in values()})
    print(sorted({x % 2 async for x in values()}))
    print([x + y async for x in values() for y in range(2) if y])
    print([[y async for y in values() if y == x] for x in range(2)])
coro = run(); count = 0
while True:
    try: coro.send(None); count += 1
    except StopIteration:
        print('suspensions', count)
        break
''',
              '''[2, 6] 99
{0: 1, 1: 2, 2: 3, 3: 4}
[0, 1]
[1, 2, 3, 4]
[[0], [1]]
suspensions 34
''')

check_program('''async def value(x): return x * 2
g = (await value(x) for x in range(3))
async def run():
    print([x async for x in g])
try: run().send(None)
except StopIteration: print('complete')
def fail(): raise StopIteration('element')
try: [fail() for i in range(1)]
except StopIteration as error: print(error)
try: next(fail() for i in range(1))
except RuntimeError as error: print(error)
async def source(): yield 1
async def run_error():
    try: [fail() async for i in source()]
    except StopIteration as error: print('async comprehension', error)
try: run_error().send(None)
except StopIteration: print('finished')
''',
              '''[0, 2, 4]
complete
element
generator raised StopIteration
async comprehension element
finished
''')

check_program('''class Pause:
    def __await__(self):
        value = yield 'waiting'
        return value
async def values():
    yield await Pause()
    yield 2
async def run():
    g = values()
    print(aiter(g) is g)
    print(await anext(g, 'default'))
    print(await anext(g))
    print(await anext(g, 'default'))
    try: await anext(g)
    except StopAsyncIteration: print('finished')
coro = run()
print(coro.send(None))
try: coro.send(7)
except StopIteration as error: print(error.value)
class Sequence:
    def __aiter__(self): return self
    async def __anext__(self):
        await Pause()
        raise StopAsyncIteration
op = anext(Sequence(), ('default', 42))
print(type(op).__name__, op.__await__() is op, iter(op) is op, next(op))
try: op.send(None)
except StopIteration as error: print(error.value)
''',
              '''True
waiting
7
2
default
finished
None
anext_awaitable True True waiting
('default', 42)
''')

check_program('''class Pause:
    def __await__(self): yield 'waiting'
async def values():
    await Pause()
    yield 1
g = values(); op = g.asend(None)
print(next(op), g.ag_running)
for other in [g.asend(None), g.athrow(ValueError), g.aclose()]:
    try: other.throw(KeyError)
    except RuntimeError as error: print(error)
    try: other.send(None)
    except RuntimeError as error: print(error)
print(op.close(), g.ag_running)
try: next(g.__anext__())
except StopAsyncIteration: print('closed')
''',
              '''waiting True
anext(): asynchronous generator is already running
cannot reuse already awaited __anext__()/asend()
athrow(): asynchronous generator is already running
cannot reuse already awaited aclose()/athrow()
aclose(): asynchronous generator is already running
cannot reuse already awaited aclose()/athrow()
None False
closed
''')

check_program('''events = []
class Pause:
    def __await__(self):
        value = yield 'waiting'
        return value
async def values():
    try:
        sent = yield 1
        yield sent
        yield await Pause()
    finally:
        events.append('closed')
g = values()
print(type(g).__name__, g.__name__, g.__aiter__() is g, g.ag_running)
for op in [g.__anext__(), g.asend(7), g.__anext__()]:
    print(type(op).__name__, op.__await__() is op, iter(op) is op)
    try:
        print(op.send(None), g.ag_running, g.ag_await is not None)
        op.send(42)
    except StopIteration as error:
        print('value', error.value, g.ag_running, g.ag_await is None)
    try: op.send(None)
    except RuntimeError as error: print(error)
try: g.__anext__().send(None)
except StopAsyncIteration: print('finished', events)
try: g.aclose().send(None)
except StopIteration: print('closed again')
''',
              '''async_generator values True False
async_generator_asend True True
value 1 False True
cannot reuse already awaited __anext__()/asend()
async_generator_asend True True
value 7 False True
cannot reuse already awaited __anext__()/asend()
async_generator_asend True True
waiting True True
value 42 False True
cannot reuse already awaited __anext__()/asend()
finished ['closed']
closed again
''')

check_program('''class Pause:
    def __await__(self): yield 'step'
async def values():
    for i in range(3):
        await Pause()
        yield i
async def run():
    result = []
    async for item in values(): result.append(item)
    else: result.append('done')
    return result
coro = run()
while True:
    try: print(coro.send(None))
    except StopIteration as error:
        print(error.value)
        break
''',
              '''step
step
step
[0, 1, 2, 'done']
''')

check_program('''class Pause:
    def __await__(self): yield 'cleanup'
async def values():
    try:
        try: yield 1
        except ValueError as error: yield str(error)
    finally:
        await Pause()
        print('finally')
g = values()
try: next(g.__anext__())
except StopIteration as error: print(error.value)
try: next(g.athrow(ValueError('thrown')))
except StopIteration as error: print(error.value)
closer = g.aclose()
print(next(closer), g.ag_running)
try: next(g.__anext__())
except RuntimeError as error: print(error)
try: next(closer)
except StopIteration as error: print(error.value, g.ag_running)
try: next(closer)
except RuntimeError as error: print(error)
''',
              '''1
thrown
cleanup True
anext(): asynchronous generator is already running
finally
None False
cannot reuse already awaited aclose()/athrow()
''')

check_program('''async def values(error):
    yield 1
    raise error
for exception in [StopIteration('sync'), StopAsyncIteration('async')]:
    g = values(exception)
    try: next(g.__anext__())
    except StopIteration as error: print(error.value)
    try: next(g.__anext__())
    except RuntimeError as error: print(error, type(error.__cause__).__name__)
async def ignores_close():
    try: yield 1
    except GeneratorExit: yield 2
g = ignores_close()
try: next(g.__anext__())
except StopIteration: pass
try: next(g.aclose())
except RuntimeError as error: print(error)
try: next(g.aclose())
except (StopIteration, StopAsyncIteration) as error: print(type(error).__name__)
try: next(g.__anext__())
except StopAsyncIteration: print('exhausted')
''',
              '''1
async generator raised StopIteration StopIteration
1
async generator raised StopAsyncIteration StopAsyncIteration
async generator ignored GeneratorExit
StopAsyncIteration
exhausted
''')

check_program('''class A:
    __match_args__ = ("p",)
    @property
    def p(self): raise AttributeError("nope")
class B:
    __match_args__ = ["x"]
class E:
    __match_args__ = (1,)
    x = 0
def t(v):
    match v:
        case {"a": 1, **rest}: return ("dict", rest)
        case [1, *_, 9]: return "ends"
        case [*init, last] if last == 3: return ("init", init)
        case (1 | 2) as n, *_: return ("or-as", n)
        case A(1): return "A1"
        case A(): return "A"
        case 1: return "one"
        case _: return "default"
for v in [dict(a=1, b=2), dict(b=2), [1, 5, 9], [1, 2, 3], (2, 0), A(), True, 1.0, "123", b"abc", {1: 2}]:
    try: print(t(v))
    except Exception as e: print(type(e).__name__, e)
for v in [B(), E()]:
    try:
        match v:
            case B(1) | E(1): print("matched")
    except Exception as e: print(type(e).__name__, e)
def closure():
    match [10, 20]:
        case [a, b]: pass
    return lambda: a + b
print(closure()())
class K:
    match {"x": 5}:
        case {"x": value}: pass
print(K.value)
class Priv:
    def m(self, v):
        match v:
            case [__hidden]: return __hidden
print(Priv().m([3]))
async def co(v):
    match v:
        case [x]: return x
c = co([7])
try: c.send(None)
except StopIteration as s: print("co", s.value)
def g():
    match (yield):
        case 1: yield "one"
        case other: yield ("other", other)
x = g(); next(x); print(x.send(2))
match 5:
    case 1: print("no")
print("after nomatch")
for v in [0, 0.0, -0, 1e0, 1j, -1j, 1-1j, -0.5+2j]:
    match v:
        case -0.0: print("zero", v)
        case 1-1j: print("cx", v)
        case -0.5+2j: print("cx2", v)
        case 1.0: print("onef", v)
        case _: print("other", v)
match {"a": 1, "b": 2}:
    case {"b": b, "a": a}: print(a, b)
from_mod = 3
match 3:
    case int(real=r, imag=i): print(r, i)
match "x":
    case str(s): print(s)
match (1, 2):
    case [a, b] | (b, a, _): print(a, b)
match [1, [2, [3]]]:
    case [_, [_, [z]]]: print(z)
def deep():
    match 1:
        case 1:
            return "ret"
    return "no"
print(deep())
for i in range(3):
    match i:
        case 1: continue
        case 2: break
    print("i", i)
''',
              '''('dict', {'b': 2})
default
ends
('init', [1, 2])
('or-as', 2)
A
one
one
default
default
default
TypeError B.__match_args__ must be a tuple (got list)
TypeError __match_args__ elements must be strings (got int)
30
5
3
co 7
('other', 2)
after nomatch
zero 0
zero 0.0
zero 0
onef 1.0
other 1j
other (-0-1j)
cx (1-1j)
cx2 (-0.5+2j)
1 2
3 0
x
1 2
3
ret
i 0
''')

check_program('''class D(dict):
    def get(self, key, default=None):
        print("get", key)
        return super().get(key, default)
class L(list): pass
class A:
    __match_args__ = ("p",)
    @property
    def p(self): raise AttributeError("nope")
class B:
    __match_args__ = ["x"]
class E:
    __match_args__ = (1,)
    x = 0
def t(v):
    match v:
        case {"a": 1, **rest}: return ("dict", rest)
        case [1, *_, 9]: return "ends"
        case [*init, last] if last == 3: return ("init", init)
        case (1 | 2) as n, *_: return ("or-as", n)
        case A(1): return "A1"
        case A(): return "A"
        case 1: return "one"
        case _: return "default"
for v in [D(a=1, b=2), D(b=2), L([1, 5, 9]), [1, 2, 3], (2, 0), A(), True, 1.0, "123", b"abc", {1: 2}]:
    try: print(t(v))
    except Exception as e: print(type(e).__name__, e)
for v in [B(), E()]:
    try:
        match v:
            case B(1) | E(1): print("matched")
    except Exception as e: print(type(e).__name__, e)
def closure():
    match [10, 20]:
        case [a, b]: pass
    return lambda: a + b
print(closure()())
class K:
    match {"x": 5}:
        case {"x": value}: pass
print(K.value)
class Priv:
    def m(self, v):
        match v:
            case [__hidden]: return __hidden
print(Priv().m([3]))
async def co(v):
    match v:
        case [x]: return x
c = co([7])
try: c.send(None)
except StopIteration as s: print("co", s.value)
def g():
    match (yield):
        case 1: yield "one"
        case other: yield ("other", other)
x = g(); next(x); print(x.send(2))
match 5:
    case 1: print("no")
print("after nomatch")
for v in [0, 0.0, -0, 1e0, 1j, -1j, 1-1j, -0.5+2j]:
    match v:
        case -0.0: print("zero", v)
        case 1-1j: print("cx", v)
        case -0.5+2j: print("cx2", v)
        case 1.0: print("onef", v)
        case _: print("other", v)
match {"a": 1, "b": 2}:
    case {"b": b, "a": a}: print(a, b)
from_mod = 3
match 3:
    case int(real=r, imag=i): print(r, i)
match "x":
    case str(s): print(s)
match (1, 2):
    case [a, b] | (b, a, _): print(a, b)
match [1, [2, [3]]]:
    case [_, [_, [z]]]: print(z)
def deep():
    match 1:
        case 1:
            return "ret"
    return "no"
print(deep())
for i in range(3):
    match i:
        case 1: continue
        case 2: break
    print("i", i)
''',
              '''get a
('dict', {'b': 2})
get a
default
ends
('init', [1, 2])
('or-as', 2)
A
one
one
default
default
default
TypeError B.__match_args__ must be a tuple (got list)
TypeError __match_args__ elements must be strings (got int)
30
5
3
co 7
('other', 2)
after nomatch
zero 0
zero 0.0
zero 0
onef 1.0
other 1j
other (-0-1j)
cx (1-1j)
cx2 (-0.5+2j)
1 2
3 0
x
1 2
3
ret
i 0
''')

check_program('''def gen(exc):
    try:
        yield "body"
        if exc: raise exc
        yield "after"
    except* ValueError as e:
        yield ("v", repr(e))
        raise KeyError("from-v")
    except* TypeError as e:
        yield ("t", repr(e))
    else:
        yield "else"
    finally:
        yield "finally"
for exc in [None, ValueError(1), TypeError(2), ExceptionGroup("g", [ValueError(1), TypeError(2), OSError(3)]), OSError(4)]:
    out = []
    try:
        for item in gen(exc): out.append(item)
    except BaseException as err: out.append(("raised", repr(err)))
    print(out)
async def co():
    try:
        raise ExceptionGroup("a", [ValueError(1), TypeError(2)])
    except* ValueError as e:
        await sleep()
        print("async v", repr(e))
    except* TypeError as e:
        print("async t", repr(e))
class sleep:
    def __await__(self): yield
c = co()
try:
    c.send(None); c.send(None)
except StopIteration: print("done")
def g2():
    try:
        raise ValueError(1)
    except* ValueError:
        yield 1
        raise
try: list(g2())
except ExceptionGroup as e: print("g2", repr(e))
def g3():
    for i in range(2):
        try:
            yield i
            raise ExceptionGroup("x", [ValueError(i)])
        except* ValueError as e:
            yield repr(e)
print(list(g3()))
''',
              '''['body', 'after', 'else', 'finally']
['body', ('v', "ExceptionGroup('', (ValueError(1),))"), 'finally', ('raised', "KeyError('from-v')")]
['body', ('t', "ExceptionGroup('', (TypeError(2),))"), 'finally']
['body', ('v', "ExceptionGroup('g', [ValueError(1)])"), ('t', "ExceptionGroup('g', [TypeError(2)])"), 'finally', ('raised', "ExceptionGroup('', [KeyError('from-v'), ExceptionGroup('g', [OSError(3)])])")]
['body', 'finally', ('raised', 'OSError(4)')]
async v ExceptionGroup('a', [ValueError(1)])
async t ExceptionGroup('a', [TypeError(2)])
done
g2 ExceptionGroup('', (ValueError(1),))
[0, "ExceptionGroup('x', [ValueError(0)])", 1, "ExceptionGroup('x', [ValueError(1)])"]
''')

check_program('''async def f():
    yield from []
''',
              '''SyntaxError: 'yield from' inside async function (<program>, line 2)
''')

check_program('''async def f():
    yield 1
    return 2
''',
              '''SyntaxError: 'return' with value in async generator (<program>, line 3)
''')

check_program('''async def f():
    if False: yield 1
    if True: return 2
''',
              '''SyntaxError: 'return' with value in async generator (<program>, line 3)
''')
