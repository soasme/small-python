"""Differential checks for the implemented subset, not CPython's test suite."""

from pathlib import Path
import random
import math
import struct
import subprocess
import sys
import tempfile
import textwrap

ENGINE = str(Path(sys.argv[1]).resolve())
CASES = [
    """
def factory():
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
""",

    "print('Hello, world!')",
    "print(None, True, False, bool([]), bool([0]))",
    "print(1 + 2 * 3, (1 + 2) * 3, -2**2, (-2)**2, 2**-2, 2**3**2)",
    "print(-7 // 3, -7 % 3, 7 // -3, 7 % -3, -7 // -3, -7 % -3)",
    "print(0xff, 0o17, 0b1010, 1_000, 1.25e2)",
    "print(1 << 5, -9 >> 2, 15 & 6, 15 | 16, 9 ^ 3, ~7)",
    "print(1 < 2 < 3, 1 < 2 > 3, 3 > 2 >= 2, 1 == True, None is None)",
    "print(0 and missing, 4 or missing, not 1 == 2, not [] and True)",
    "print(1 if True else missing, missing if False else 2)",
    "print('a' 'b', 'ab' * 3, 3 * 'x', 'a' + 'b', len('hé🙂'), 'hé🙂'[2])",
    "print('a\\nb', 'c\\td', 'quote: \\'', '\\\\', '\\x41')",
    "print('''hello\nworld''')",
    """
    for args in [(), ('bad',), ('bad', ('path/file.py', 2, 3, 'line')),
                 ('bad', ('path/file.py', 2, 3, 'line', 2, 4)), (1, 2, 3)]:
        error = SyntaxError(*args)
        print(str(error), error.args, error.msg, error.filename, error.lineno,
              error.offset, error.text, error.end_lineno, error.end_offset)
    error.__init__('old', ('f', 2, 3, 'line', 2, 4))
    error.__init__()
    print(error.args, error.msg, error.filename)
    error.__init__('new')
    print(error.args, error.msg, error.filename)
    for filename, line in [(None, None), (None, 0), ('', 2), (42, 2), ('f', 's'), ('f', None)]:
        error = SyntaxError('bad')
        error.filename = filename
        error.lineno = line
        print(str(error))
    for source in ['€ = 2\\n', 'x€ = 2\\n', 'if True\\n    pass\\n']:
        try: compile(source, 'path/file.py', 'exec')
        except SyntaxError as error:
            print(str(error), error.filename, error.lineno, error.offset, repr(error.text), error.end_lineno, error.end_offset)
    try:
        try: raise ValueError('context')
        except ValueError: compile('€ = 1', 'file.py', 'exec')
    except SyntaxError as error: print(type(error.__context__).__name__)
    """,
    """
    µ = 42
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
    """,
    """
    # Default deletion and readonly globals from CPython test_funcattrs.
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
    """,
    """
    calls = []
    class Descriptor:
        def __delete__(self, instance): calls.append('descriptor')
    class C:
        field = Descriptor()
        @property
        def value(self): return 42
        @value.deleter
        def value(self): calls.append('property')
    c = C()
    delattr(c, 'field')
    del c.field
    delattr(c, 'value')
    del c.value
    c.extra = 1
    print(delattr(c, 'extra'), calls)
    """,
    """
    # Factory behavior exercised by CPython test_descr.test_funny_new.
    class C:
        def __new__(cls, arg):
            if isinstance(arg, str): return [1, 2, 3]
            if isinstance(arg, int): return object.__new__(D)
            return object.__new__(cls)
    class D(C):
        def __init__(self, arg): self.foo = arg
    print(C('1'), D('1'), D(None).foo, C(1).foo, D(1).foo)
    print(type(C(1)) is D)
    class Static:
        @staticmethod
        def __new__(*args): return args
    class DerivedStatic(Static): pass
    print(Static(1, 2) == (Static, 1, 2), DerivedStatic(1, 2) == (DerivedStatic, 1, 2))
    class Class:
        @classmethod
        def __new__(*args): return args
    class DerivedClass(Class): pass
    print(Class(1, 2) == (Class, Class, 1, 2), DerivedClass(1, 2) == (DerivedClass, DerivedClass, 1, 2))
    class Plain:
        def __new__(cls, value=0):
            result = object.__new__(cls)
            result.value = value
            return result
    p = Plain(value=42)
    print(p.value, Plain.__new__(Plain, 3).value, p.__new__(Plain, 4).value)
    """,
    """
    # Invalid exception factory results from CPython test_raise.
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
    """,
    """
    calls = []
    class Get:
        def __get__(self, instance, owner):
            calls.append(('get', instance is None, owner is C))
            def create(cls, value):
                calls.append(('create', cls is C, value))
                return object.__new__(cls)
            return create
    class C:
        __new__ = Get()
        def __init__(self, value=0): calls.append(('init', value))
    C(3)
    print(calls)
    def other(cls): return 42
    C.__new__ = other
    print(C())
    del C.__new__
    print(type(C()) is C, calls)
    class InitError:
        def __init__(self): return 1
    try: InitError()
    except TypeError: print('invalid initializer result')
    def keywords(a=1, **kw): return a, kw
    print(keywords(**{'a\\x00extra': 2}))
    """,
    """
    for cause in [None, KeyError, KeyError('cause')]:
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
    """,
    """
    items = [0, 1, 2]
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
    """,
    """
    class Clear:
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
    """,
    """
    items = [(2, 'a'), (1, 'b'), (2, 'c'), (1, 'd')]
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
    """,
    """
    def f(a, b=2, /, c=3, *, d=4): return a, b, c, d
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
    """,
    """
    calls = []
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
    """,
    """
    exec(compile('1; None; 2', '<single>', 'single'))
    exec(compile('(1\\n+2); 4', '<single>', 'single'))
    exec(compile('if True:\\n    3\\n    4\\n', '<single>', 'single'))
    print(eval(compile('5', '<single>', 'single')))
    exec(compile('def f():\\n    9\\n', '<single>', 'single'))
    print(f())
    for source in ['', '1\\n2', 'if True:\\n    1\\n2']:
        try: compile(source, '<single>', 'single')
        except SyntaxError: print('invalid single input')
    """,
    """
    events = []
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
    """,
    """
    nan = float('nan')
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
    """,
    """
    big = 10**100
    for r in [range(5), range(2, 8, 2), range(big, big + 10, 3), range(-big, -big - 10, -3), range(5, 5, -1)]:
        print(r, r.start, r.stop, r.step, len(r), bool(r))
        print(list(r), list(reversed(r)), list(r[::-1]), r[1:-1], r[::-2])
        if r:
            print(r[0], r[-1], r[0] in r, r.stop in r, r.count(r[0]), r.index(r[-1]))
    r = range(-big, big, 3)
    print(r[big // 3], r[-1], next(reversed(r)), r[:5], r[-5:], r[::big])
    print(r.count(-big), r.index(-big + 3 * 10**90), r.count(big))
    print(range(0) == range(2, 2, -3), range(0, 3, 2) == range(0, 4, 2), range(1) == range(0, 1, 9))
    print(range(5).count(2.0), range(5).index(2.0), range(5).count('2'))
    print(slice(None, None, -1).indices(big), slice(-big * 2, big * 2, big).indices(big))
    print(slice(-big * 2, big * 2, -big).indices(big), slice(None, None, big).indices(5))
    class Index:
        def __index__(self): return big
    print(range(Index(), big + 2), list(range(Index(), big + 2)))
    """,
    """
    class Manager:
        def __enter__(self): print('enter'); return 42
        def __exit__(self, kind, value, tb): print('exit')
    with (Manager() as a, Manager() as b,): print(a + b)
    with (Manager()) as a: print(a)
    class AsyncManager:
        async def __aenter__(self): print('aenter'); return 3
        async def __aexit__(self, kind, value, tb): print('aexit')
    async def run():
        async with (
            AsyncManager() as a,
            AsyncManager() as b,
        ): return a + b
    try: run().send(None)
    except StopIteration as error: print(error.value)
    """,
    """
    class BadEnter:
        def __aenter__(self): return 1
        def __aexit__(self, *args): print('wrong exit')
    class BadExit:
        async def __aenter__(self): return self
        def __aexit__(self, *args): return 1
    async def run(manager):
        async with manager:
            raise ValueError('body')
    for manager in [BadEnter(), BadExit()]:
        try: run(manager).send(None)
        except TypeError as error:
            print(error, type(error.__context__).__name__)
    """,
    """
    import builtins
    print(builtins.int is int, builtins.__dict__['len'] is len)
    events = []
    class Module:
        value = 42
    def importer(name, globals, locals, fromlist, level):
        events.append((name, fromlist, level, globals is locals))
        return Module()
    namespace = {'__builtins__': {'__import__': importer}}
    exec('import arbitrary as module; from elsewhere import value as answer', namespace)
    print(namespace['module'].value, namespace['answer'], events)
    try: exec('import arbitrary', {'__builtins__': {}})
    except ImportError as error: print(error)
    """,
    """
    class Pause:
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
    """,
    """
    events = []
    class Sequence:
        def __aiter__(self):
            events.append('iterator')
            self.i = 0
            return self
        async def __anext__(self):
            if self.i == 3: raise StopAsyncIteration
            self.i += 1
            return self.i
    source = Sequence()
    g = (x * 2 async for x in source)
    print(type(g).__name__, events)
    async def run():
        print([x async for x in g])
        print(events)
        async def immediate(x): return x + 1
        other = (await immediate(x) for x in range(3))
        print(type(other).__name__, [x async for x in other])
    coro = run()
    try: coro.send(None)
    except StopIteration: print('complete')
    """,
    """
    async def value(x): return x * 2
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
    """,
    """
    class Pause:
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
    """,
    """
    class Pause:
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
    """,
    """
    events = []
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
    """,
    """
    class Pause:
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
    """,
    """
    class Pause:
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
    """,
    """
    async def values(error):
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
    """,
    """
    events = []
    class Pause:
        def __await__(self):
            events.append('pause')
            value = yield 'waiting'
            return value
    async def child():
        return await Pause()
    async def main():
        events.append('start')
        try:
            value = 2 + await child()
            return f'{value=}'
        finally:
            events.append('finally')
    coro = main()
    print(type(coro).__name__, coro.__name__, events, coro.cr_running, coro.cr_suspended)
    wrapper = coro.__await__()
    print(iter(wrapper) is wrapper, next(wrapper), events, coro.cr_suspended)
    try:
        wrapper.send(5)
    except StopIteration as error:
        print(error.value, events, coro.cr_suspended)
    try:
        coro.send(None)
    except RuntimeError as error:
        print(str(error))
    print(coro.close())
    """,
    """
    class Pause:
        def __await__(self):
            try:
                yield 1
            except ValueError as error:
                print('caught', error)
                return 7
            finally:
                print('cleanup')
    async def run():
        return await Pause()
    coro = run(); print(coro.send(None))
    try:
        coro.throw(ValueError('bad'))
    except StopIteration as error:
        print(error.value)
    coro = run(); print(coro.send(None)); print(coro.close())
    async def immediate(value=3):
        return value
    async def composed():
        return [await immediate(), await immediate(5)]
    coro = composed()
    try:
        coro.send(None)
    except StopIteration as error:
        print(error.value)
    """,
    """
    async def f():
        raise StopIteration('escaped')
    coro = f()
    try:
        coro.send(None)
    except RuntimeError as error:
        print(error, type(error.__cause__).__name__)
    async def empty():
        pass
    coro = empty()
    try:
        iter(coro)
    except TypeError:
        print('not iterable')
    try:
        coro.send(1)
    except TypeError:
        print('not started')
    coro.close()
    """,
    """
    class Pause:
        def __await__(self): yield 'waiting'
    async def child():
        await Pause()
    async def parent(value):
        return await value
    value = child()
    print(value.cr_await is None)
    print(value.send(None), value.cr_await is not None)
    other = parent(value)
    try:
        other.send(None)
    except RuntimeError as error:
        print(error)
    value.close()
    print(value.cr_await is None)
    value = child(); other = parent(value)
    print(other.send(None), other.cr_await is value)
    other.close()
    print(other.cr_await is None, value.cr_await is None)
    """,
    """
    events = []
    class Pause:
        def __await__(self):
            yield 'step'
    class Sequence:
        def __init__(self): self.index = 0
        def __aiter__(self): return self
        async def __anext__(self):
            await Pause()
            if self.index == 3: raise StopAsyncIteration
            value = self.index
            self.index += 1
            return value
    async def run():
        result = []
        async for value in Sequence():
            if value == 1: continue
            result.append(value)
        else:
            events.append('complete')
        async for value in Sequence():
            result.append(value)
            break
        else:
            events.append('wrong')
        try:
            async for value in Sequence():
                raise StopAsyncIteration('body')
        except StopAsyncIteration:
            events.append('body error')
        return result
    coro = run()
    while True:
        try:
            print(coro.send(None))
        except StopIteration as error:
            print(error.value, events)
            break
    """,
    """
    events = []
    class Pause:
        def __await__(self):
            try:
                yield 1
            finally:
                events.append('closed')
    class Sequence:
        def __aiter__(self): return self
        async def __anext__(self): return await Pause()
    async def run():
        try:
            async for value in Sequence(): pass
        finally:
            events.append('outer')
    coro = run()
    print(coro.send(None))
    print(coro.close(), events)
    """,
    """
    class Pause:
        def __init__(self, label): self.label = label
        def __await__(self): yield self.label
    class Manager:
        def __init__(self, name): self.name = name
        async def __aenter__(self):
            await Pause('enter ' + self.name)
            return self
        async def __aexit__(self, kind, value, tb):
            print('exit', self.name, kind.__name__ if kind else None)
            await Pause('exit ' + self.name)
            return self.name == 'B'
    async def run():
        async with Manager('A') as a, Manager('B') as b:
            print(a.name, b.name)
            raise ValueError('body')
        for i in range(3):
            async with Manager('loop'):
                if i == 0: continue
                break
        async with Manager('return'):
            return 42
    coro = run()
    while True:
        try: print(coro.send(None))
        except StopIteration as error:
            print('result', error.value)
            break
    """,
    """
    events = []
    class Pause:
        def __await__(self): yield 'pause'
    class Manager:
        async def __aenter__(self): return self
        async def __aexit__(self, kind, value, tb):
            events.append(kind.__name__ if kind else None)
            await Pause()
            return True
    async def run():
        async with Manager():
            raise ValueError('first')
        return 3
    coro = run(); print(coro.send(None), events)
    try: coro.throw(KeyError('second'))
    except KeyError as error:
        print(error, type(error.__context__).__name__, error.__context__)
    coro = run(); print(coro.send(None)); print(coro.close())
    async def cancelled():
        async with Manager():
            await Pause()
    coro = cancelled(); print(coro.send(None))
    try: coro.close()
    except RuntimeError as error: print(error)
    print(coro.close(), events)
    """,
    """
    events = []
    class Manager:
        def __init__(self, name): self.name = name
        async def __aenter__(self):
            events.append(self.name)
            if self.name == 'bad': raise ValueError('entry')
            return [1]
        async def __aexit__(self, kind, value, tb):
            events.append((self.name, kind.__name__, str(value)))
    async def run():
        async with Manager('outer'), Manager('bad'): pass
    coro = run()
    try: coro.send(None)
    except ValueError as error: print(error, events)
    async def unpack():
        async with Manager('unpack') as (a, b): pass
    coro = unpack()
    try: coro.send(None)
    except ValueError as error: print(error, events[-1][0:2])
    """,
    r"""
    a = b'\x00\x7f\x80\xff\n\t\r\'"'
    print(a, str(a), repr(a), len(a), list(a), tuple(reversed(a)))
    print(a[0], a[-1], a[1:-1], a[::-2], a[:0])
    print(a + b'z', b'ab' * 3, 2 * b'x', b'x' * 0, bool(b''), bool(a))
    print(b'a' < b'b', b'a' == 'a', b'a' != 'a', b'\xff' > b'z')
    print(0 in a, 255 in a, b'\x7f\x80' in a, b'' in a, b'zz' not in a)
    print(B'ab' b'cd', br'\xff', RB'\n', b'\101\377', ord(b'\xff'))
    print(bytes(), bytes(3), bytes([0, 127, 128, 255]), bytes(range(3)), bytes(a) is a)
    print(int(b'123456789012345678901234567890'), int(b'ff', 16), float(b'2.5'))
    print({b'x': 1, b'y': 2}[b'x'], b'x' in {b'x': 1})
    class Byte:
        def __index__(self): return 65
    class ByteSource:
        def __bytes__(self): return b'converted'
    print(bytes([Byte()]), bytes(ByteSource()))
    """,
    "print(len('a\\x00b'), 'a\\x00b'[1] == '\\x00', 'b' in 'a\\x00b')",
    "print('bc' in 'abcd', 'xy' not in 'abcd', '' in '', 'a' < 'b')",
    "print([1, 2] + [3], [1] * 3, (1, 2) + (3,), (1,) * 2)",
    "print([1, 2] == [1, 2], [1] != [2], (1,) != [1], [] == [])",
    "a = [1, 2, 3]; a[-1] = 7; a.append(9); print(a, a.pop(), a.pop(0), a)",
    "a = []; a.append(a); print(a)",
    "a = []; b = a; a += [1, 2]; print(a, b, a is b)",
    "a = [1, 2]; a += a; print(a)",
    """
    a = [1, 2]; b = a; a *= 3; print(a, a is b)
    a += iter((7, 8)); print(a)
    a *= 0; print(a, b, a is b)
    a.append(a); a *= 2; print(a)
    """,
    """
    class Count:
        def __index__(self): return 2
    a = [4]; b = a; a *= Count(); print(a, a is b)
    class Base:
        def __add__(self, other): print('add'); return NotImplemented
        def __radd__(self, other): print('radd'); return 12
        def __iadd__(self, other): print('iadd'); return NotImplemented
    class Sub(Base):
        def __radd__(self, other): print('sub radd'); return 14
    print(Base() + Sub())
    a = Base(); a += Sub(); print(a)
    print(1 + Base())
    class Format:
        def __rmod__(self, other): return 'wrong'
        def __str__(self): return 'formatted'
    print('%s' % Format())
    """,
    """
    for text in ['', 'a', '\\n', 'a\\nb\\r\\nc\\r', '\\v\\f\\x1c\\x1d\\x1e',
                 'é\\x85🙂\\u2028尾\\u2029']:
        print(text.splitlines(), text.splitlines(True), text.splitlines(keepends=True))
    """,
    "d = {'a': 1, 'b': 2}; d['c'] = 3; d['a'] += 4; print(d, d['a'])",
    "d = {1: 'first', True: 'second'}; print(d, len(d), 1 in d)",
    "d = {'a': 1, 'b': 2}; print(d.get('x'), d.get('x', 8), list(d.keys()), list(d.values()), list(d.items()))",
    "d = {}; d['self'] = d; print(d)",
    "print(list(range(5)), list(range(5, -2, -2)), len(range(10, 0, -3)), bool(range(0)))",
    "print(tuple(range(3)), list('abc'), list((1, 2)), list({'x': 3}))",
    "print(sum(range(10)), sum([1, 2], 10), min([3, 1, 2]), max(1, 5, 3))",
    "print(all([]), any([]), all([1, 2]), any([0, 3]), all([0, 1]))",
    "print(int(' 42 '), int(-1.9), float('2.5'), str(42), repr([1]), abs(-3), abs(-2.5))",
    "print(int(), float(), bool(), str(), list(), tuple(), dict())",
    "x = 5; x += 2; x *= 3; x -= 1; x %= 6; x /= 2; print(x)",
    """
    if False:
        print('no')
    elif 2 > 1:
        print('yes')
    else:
        print('no')
    """,
    """
    x = 0
    while x < 5:
        x += 1
        if x == 2:
            continue
        print(x)
    else:
        print('done')
    """,
    """
    for x in range(5):
        if x == 3:
            break
        print(x)
    else:
        print('bad')
    for x in []:
        print('bad')
    else:
        print('empty')
    """,
    """
    for x in range(3):
        for y in range(3):
            if y == 1:
                break
            print(x, y)
    """,
    """
    def fib(n):
        if n < 2:
            return n
        return fib(n - 1) + fib(n - 2)
    print(fib(12))
    """,
    """
    def make(x):
        def add(y):
            return x + y
        return add
    a = make(2)
    b = make(3)
    print(a(4), b(4), a(7))
    """,
    """
    def f(n):
        for x in range(n):
            if x == 3:
                return x
        return -1
    print(f(5), f(2))
    """,
    "def nothing(): pass\nprint(nothing())",
    """
    calls = []
    def middle():
        calls.append(1)
        return 2
    print(1 < middle() < 3, calls)
    print(4 < middle() < missing, calls)
    """,
    """
    calls = []
    a = [2]
    def index():
        calls.append('index')
        return 0
    def rhs():
        calls.append('rhs')
        return 3
    a[index()] += rhs()
    print(a, calls)
    calls = []
    a[index()] = rhs()
    print(a, calls)
    """,
    "x = (\n    1 +\n    2\n)\nprint(x)",
    "x = 1 + \\\n    2\nprint(x)",
    "# comment\n\nif True:\n    # comment\n    print(42)\n\n# last",
    "if True: print(1); print(2)\nprint(3)",
    "print(__name__)",
    "print(0.1, 0.3, 1e-4, 1e-5, 1e15, 1e16, -0.0, 1.2345678901234567)",
    "print(1.0 // 0.1, 1.0 % 0.1, -1.0 // 0.1, -1.0 % 0.1)",
    "print(9007199254740993 == 9007199254740992.0, 9007199254740993 > 9007199254740992.0, 9223372036854775807 < 9223372036854775808.0)",
    "n = float('nan'); print(n == n, n != n, n < 0, [n] == [n])",
    "print({'a': [1], 'b': 2} == {'b': 2, 'a': [1]}, {} == {}, {} != {'a': 1})",
    "print(0x_FF, 0b_101, 0o_17, 1_000.5_5)",
    "if True:\n    x = (\n        1 + 2\n    )\n    print(x)\nprint(4)",
    """
x: int = 1
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
""",
]
CASES += [
    "print(', '.join(str(i) for i in range(4))); print('a%d:%s:%r:%%' % (3, 'x', 'y'))",
    "print('**{{{}: {}}}'.format(1, 2)); print('{1}:{0}:{1}'.format('a', 'b'))",
    "code = compile('a + 2', 'generated.py', 'eval'); a = 40; print(eval(code), eval('a + 3'))",
    "code = compile('def f(x): return x + 2', 'generated.py', 'exec'); exec(code); print(f(40), eval(code))",
    "exec('value = 42'); print(value, exec('1 + 2'))",
    "print(type(True), type(1), type([]), type(type), isinstance(True, int), issubclass(bool, int))",
    "print(type(None), type((i for i in []))); a = None; b = None; print(id(a) == id(b), id(True) == id(True))",
    "print(str(ValueError('message')), repr(ValueError('message')), str(KeyError('key')))",
    """
    class C:
        def __bool__(self): return False
        def __str__(self): return 'text'
        def __repr__(self): return 'C()'
    c = C()
    print(bool(c), str(c), repr(c), [c], isinstance(c, C), isinstance(c, object))
    setattr(c, 'x', 3)
    print(getattr(c, 'x'), getattr(c, 'missing', 4), hasattr(c, 'x'), hasattr(c, 'missing'))
    del c.x
    print(hasattr(c, 'x'))
    """,
    """
    log = []
    class Manager:
        def __init__(self, name, suppress=False):
            self.name = name
            self.suppress = suppress
        def __enter__(self):
            log.append(self.name)
            return 42
        def __exit__(self, kind, value, traceback):
            log.append((self.name, kind is ValueError))
            return self.suppress
    with Manager('outer'), Manager('inner', True) as value:
        print(value)
        raise ValueError('detail')
    print(log)
    def f():
        with Manager('return'):
            return 3
    print(f())
    """,
    """
    log = []
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
    """,
    "a, (b, *c), d = [1, range(2, 6), 7]; print(a, b, c, d)",
    "a = b = []; a.append(1); print(a is b, b); a, b = b, a; print(a is b)",
    "i = 0; a = [0, 0]; i, a[i] = 1, 5; print(i, a)",
    "x = 50; print([(x, y) for x in range(4) if x for y in range(x) if y]); print(x)",
    "print({k: v for k, v in zip('ab', [1, 2])}); print(sorted({i % 3 for i in range(10)}))",
    "print(sorted({1, *range(4)}), {**{'a': 1}, 'b': 2, **{'a': 3}})",
    "print(True & False, True | False, True ^ True, True & 3)",
    "it = iter([1]); print(next(it), next(it, 42), next(it, 43)); print(iter(it) is it)",
    "it = iter(range(10)); print(list(zip(it, it)), next(it, None)); print(list(enumerate('ab', 3)))",
    "print(list(reversed([1, 2, 3])), list(reversed('hé🙂')), sorted([(2, 0), (1, 2), (1, 1)]))",
    """
    def f(a, /, b=2, *args, c=3, **kw):
        return a, b, args, c, kw
    print(f(1, 4, 5, 6, c=7, a=8, d=9))
    print(f(*(1,), **{'b': 4, 'c': 5}))
    def remember(x, items=[]):
        items.append(x)
        return items
    print(remember(1), remember(2))
    print((lambda a, *, b=2: a+b)(3, b=4))
    """,
    """
    log = []
    def mark(x):
        log.append(x)
        return x
    def f(a, b):
        return a, b
    print(f(b=mark(2), *[mark(1)]), log)
    """,
    """
    class Base:
        value = 4
        def f(self, n=1):
            return self.value + n
    class Child(Base):
        def __init__(self, value):
            self.value = value
        def __call__(self, x):
            return self.f(x)
    a = Child(value=10)
    method = a.f
    a.value += 2
    print(method(), a(3), Base.value)
    """,
    """
    x = 3
    class C:
        x = 4
        def f(self):
            return x
    print(C.x, C().f())
    """,
    """
    class Counter:
        def __init__(self, n):
            self.n = n
        def __iter__(self):
            return self
        def __next__(self):
            if not self.n:
                raise StopIteration
            self.n -= 1
            return self.n
    it = Counter(4)
    print(iter(it) is it, next(it), list(it), next(it, 42))
    print(sum(Counter(5)), any(Counter(1)), all(Counter(2)))
    """,
    """
    class Problem(ValueError):
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
    """,
    """
    def f():
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
    """,
    """
    try:
        1 / 0
    except ArithmeticError as e:
        print('caught')
    else:
        print('wrong')
    try:
        e
    except NameError:
        print('deleted')
    """,
    """
    def make(n):
        return ((i, j) for i in range(n) for j in range(i) if j % 2 == 0)
    g = make(4)
    print(next(g), list(g), list(g))
    x = 3
    g = (i * x for i in range(x))
    x = 4
    print(list(g))
    """,
    """
    def f():
        g = ((saved := i*i) for i in range(3))
        print(next(g), saved, list(g), saved)
        return [(last := x) for x in range(3)], last
    print(f())
    """,
    """
    def stop():
        raise StopIteration
    g = (stop() for x in range(1))
    try:
        next(g)
    except RuntimeError:
        print('converted')
    print(list(g))
    """,
]
CASES += [
    """
    def g(n):
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
    """,
    """
    def sub():
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
    """,
    """
    def g():
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
    """,
    """
    def g():
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
    """,
    """
    def g():
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
    """,
    """
    class C:
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
    """,
    """
    def mark(x): print('mark', x); return x
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
    """,
    """
    def g():
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
    """,
]
CASES += [
    """
    def g():
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
    """,
    """
    def g(d):
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
    """,
    """
    def g():
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
    """,
]
CASES += [
    """
    for start in [None, -20, -3, -1, 0, 2, 5, 20]:
        for stop in [None, -20, -3, -1, 0, 2, 5, 20]:
            for step in [None, -20, -2, -1, 1, 2, 20]:
                s = slice(start, stop, step)
                print(s.indices(5), [0,1,2,3,4][s], (0,1,2,3,4)[s], 'aé🙂bc'[s])
                a = list(range(5))
                a[s] = [10 + i for i in a[s]]
                print(a)
                del a[s]
                print(a)
    for start in [-20, -1, 0, 2, 20]:
        for stop in [-20, -1, 0, 2, 20]:
            a = list(range(5))
            a[start:stop] = a
            print(a)
    """,
    """
    class Index:
        def __init__(self, n): self.n = n
        def __index__(self): print('index', self.n); return self.n
    a = [0,1,2,3,4]
    print(a[Index(-1)], a[Index(1):Index(4):Index(2)])
    a[Index(1):Index(4):Index(2)] = [10, 30]
    print(a)
    class Keys:
        def __getitem__(self, key): return key
    print(Keys()[1:5:2, 3], slice(2), slice(1,2,3).start, slice(1,2,3).stop, slice(1,2,3).step)
    print(slice(1,2,3) == slice(1,2,3), {slice(1): 42}[slice(1)])
    """,
    """
    a = [0,1,2,3,4]
    def replacement():
        a[:] = [10,11]
        yield 9
    a[1:4] = replacement()
    print(a)
    def g():
        yield [0,1,2,3,4][(yield 1):(yield 2):(yield 3)]
    a = g()
    print(next(a), a.send(0), a.send(5), a.send(2), list(a))
    """,
]
CASES += [
    """
    print(1, 2, sep=':', end='!')
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
    """,
]
CASES += [
    """
    def g(data):
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
    """,
]
CASES += [
    """
    x = 10
    def outer(x):
        def inc():
            nonlocal x
            x += 1
            return x
        def dec():
            nonlocal x
            x -= 1
            return x
        return inc, dec
    inc, dec = outer(0)
    print(inc(), inc(), dec(), dec(), x)
    def scope():
        x = 1
        def global_scope():
            global x
            def indirect(): return lambda: x
            x = 12
            return indirect()
        def local_scope(): return x
        return global_scope(), local_scope
    a, b = scope()
    print(a(), b(), x)
    """,
    """
    def outer(x):
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
    """,
    """
    x = 10
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
    """,
    """
    x = 1
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
    """,
    """
    x = 0
    def f():
        global x
        print([(x := i) for i in range(3)])
    f()
    print(x)
    def outer():
        x = 0
        def inner():
            nonlocal x
            return [(x := i) for i in range(3)]
        print(inner(), x)
    outer()
    def g():
        global created
        def created(): return 42
    g()
    print(created())
    """,
]
CASES += [
    """
    class C:
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
    """,
    "print(__debug__, [__debug__ for x in range(2)])",
]
CASES += [
    """
    events = []
    def decorator(label):
        events.append(('evaluate', label))
        def apply(fn):
            events.append(('apply', label))
            return fn
        return apply
    def default():
        events.append('default')
        return 17
    @decorator('outer')
    @decorator('inner')
    def f(x=default()):
        return x
    @decorator('class')
    class C:
        events.append('body')
    print(events, f(), C.__name__)
    """,
    """
    events = []
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
    """,
    """
    def g():
        @(yield 'decorator')
        def f(x=3):
            return x
        yield f()
    it = g()
    print(next(it))
    print(it.send(lambda f: f))
    """,
    """
    class Base:
        @classmethod
        def cls(cls, x=4):
            return cls.__name__, x
        @staticmethod
        def stat(x=5):
            return x
        def instance(self):
            return self
    class Child(Base):
        pass
    b = Base()
    c = Child()
    print(Base.cls(), b.cls(x=7), Child.cls(), c.cls())
    print(Base.stat(), b.stat(x=2), Child.stat(9), c.stat())
    print(c.cls.__self__ is Child, c.instance.__self__ is c)
    sm = staticmethod(lambda x: x + 1)
    print(sm(10), sm.__func__ is sm.__wrapped__, callable(sm), callable(classmethod(lambda x: x)))
    """,
    """
    class C:
        @property
        def x(self):
            'the value'
            return self._x
        @x.setter
        def x(self, value):
            self._x = value
        @x.deleter
        def x(self):
            del self._x
    c = C()
    c.x = 13
    print(c.x, C.x.__doc__, C.x.fget.__name__, C.x.fset.__name__)
    del c.x
    print(hasattr(c, 'x'), C.x.fdel.__name__)
    """,
    """
    class Descriptor:
        def __get__(self, obj, owner):
            if obj is None:
                return owner.__name__
            return obj._value
        def __set__(self, obj, value):
            obj._value = value + 1
        def __delete__(self, obj):
            del obj._value
    class C:
        x = Descriptor()
    c = C()
    c.x = 20
    print(C.x, c.x)
    del c.x
    print(hasattr(c, 'x'))
    """,
    """
    class Descriptor:
        def __get__(self, obj, owner):
            return 10
    class C:
        x = Descriptor()
    c = C()
    print(c.x)
    c.x = 12
    print(c.x, C.x)
    del c.x
    print(c.x)
    """,
    "print('{{{name}}} {0} {name}'.format(5, name='value'))",
    """
    def outer():
        free = 11
        def inner(a):
            nonlocal free
            b = 2
            snapshot = locals()
            b = 3
            free += 1
            print(snapshot, a, b, free)
        inner(1)
    outer()
    """,
    """
    class C:
        z = 1
        def __dir__(self):
            return ('z', 'a', 'q')
    print(dir(C()))
    """,
]

CASES += [
    "x = 3; print(f'hello {x}, {x*2=}, {x!r}')",
    "print(f'{12:04d} {3.14159:.2f} {255:#06x} {0.125:.1%}')",
    "print(f'{3:{4}}', f'{-42:=8}', f'{42:+08}', f'{255:#08X}')",
    "print(format('é🙂abc', '🙂^9.3s'), format('x', '05'), format(1.0, '.3'))",
    "print(ascii('é🙂'), f'{\"é🙂\"!a}', '\\u00e9', '\\U0001f642', '\\377', r'\\n', u'hi')",
    "print('a' f'{1}' 'b', f'', f'{{{1}}}', f'{1 == 2}', f'{1 != 2}')",
    "print(f'{f\"{1+2}\"!r}', f'{ {\"x\": 1}[\"x\"] }')",
    "print(f'{2 # a field comment\n}', f'{(x := 3)} {x}', f'{ x = }')",
    """
    events = []
    class Value:
        def __str__(self):
            events.append('convert')
            return 'value'
        def __format__(self, spec):
            events.append(('format', spec))
            return 'formatted'
    def spec():
        events.append('spec')
        return ''
    print(f'{Value()!s:{spec()}}', events)
    events = []
    print(f'{Value():{spec()}}', events)
    """,
    """
    def g():
        yield f'a{(yield 1)}b{(yield 2)}'
        yield f'{12:{(yield 3)}}'
    x = g()
    print(next(x), x.send(4), x.send(5))
    print(next(x), x.send('04d'))
    """,
    """
    class C:
        __x = 8
        def show(self):
            return f'{self.__x} {self.__x=}'
    print(C().show())
    """,
]

CASES += [
    """
    x = 3
    g = globals()
    g['x'] = 4
    print(x, g is globals(), locals() is globals())
    def f():
        return globals() is g
    print(f(), f.__globals__ is g)
    """,
    """
    g = {'x': 5}
    l = {'x': 6}
    print(eval('x + 1', g), eval('x + 1', g, l))
    exec('y = x + 2', g, l)
    print(l['y'], 'y' in g, '__builtins__' in g)
    exec('def f(): return x', g, l)
    print(l['f'](), l['f'].__globals__ is g)
    exec('global z; z = x', g, l)
    print(g['z'], 'z' in l)
    """,
    """
    def f():
        x = 7
        print(eval('x + 1'))
        exec('x = 9')
        print(x, eval('x'))
    f()
    g = {'__builtins__': {'answer': 42}}
    print(eval('answer', g))
    exec('def f(): return answer', g)
    print(g['f']())
    """,
    """
    x = 3
    __doc__ = 'outer'
    class C:
        print('later' in locals(), __doc__)
        saved = locals()
        later = 4
        saved['added'] = 5
        del later
        print('later' in saved)
    print(C.added, C.__doc__)
    class D:
        'class documentation'
        print(__doc__)
    print(D.__doc__)
    """,
    """
    def f():
        'documentation'
    f.extra = f
    f.__dict__.update(a=1)
    f.__name__ = 'renamed'
    print(f.__name__, f.__qualname__, f.__doc__, f.extra is f, f.a)
    wrapper = staticmethod(f)
    print(wrapper.__name__ is f.__name__, wrapper.__annotations__ is f.__annotations__)
    f.__name__ = 'later'
    print(wrapper.__name__, f.__name__)
    """,
    """
    def outer():
        class C:
            def method(self): pass
        return C
    C = outer()
    print(C.__qualname__, C.method.__qualname__)
    """,
    """
    class C:
        def __getattr__(self, name): return 'missing:' + name
        @property
        def x(self): raise AttributeError('unavailable')
    print(C().x, C().y)
    print(list(map(lambda x, y: x+y, [1, 2, 3], [4, 5])))
    def stop(x):
        if x == 1: raise StopIteration
        return x
    m = map(stop, [1, 2])
    print(next(m, 'stop'), next(m))
    """,
    """
    d = {'a': 1}
    print(d.update([('b', 2)], a=3), d)
    print('{!r} {name:>4}'.format('x', name='y'))
    """,
]

CASES += [
    """
    original = TypeError
    g = {}
    exec("__builtins__['TypeError'] = 9; __builtins__['BaseException'] = 9", g)
    try:
        len(1)
    except original as error:
        print(type(error) is original)
    """,
]

CASES += [
    "print(..., ... is Ellipsis, type(...)() is ..., type(None)() is None, type(NotImplemented)() is NotImplemented)",
    """
    events = []
    class A:
        def __matmul__(self, other):
            events.append('left')
            return NotImplemented
        def __rmatmul__(self, other):
            events.append('base reflected')
            return 3
    class B(A):
        def __rmatmul__(self, other):
            events.append('derived reflected')
            return 4
    class C:
        def __rmatmul__(self, other): return 5
        def __imatmul__(self, other): return 6
    print(A() @ B(), events)
    events = []
    print(A() @ C(), events)
    c = C()
    c @= A()
    print(c)
    a = A()
    a @= B()
    print(a)
    """,
]

CASES += [
    "print(1j, 1+2j, 2j*3j, (1+2j)/(3-4j), (1+2j)**2, (1+2j)**-2)",
    "print(complex(), complex(1), complex(1, -0.0), complex(-0.0, 0), complex('-j'), complex('(1.5+2j)'))",
    "print((1+2j).real, (1+2j).imag, (1+2j).conjugate(), abs(3+4j), 1+0j == 1)",
    "print('%s' % (1+2j), (-1)**0.5, 0j**0, bool(0j), bool(1j), 1j != 1)",
    "print(complex('1_2.5+2_0j'), complex('inf'), complex('nanj'), complex('-inf-infj'))",
    """
    class C:
        def __complex__(self): return 1+2j
    class F:
        def __float__(self): return 3.5
    class I:
        def __index__(self): return 4
    print(complex(C()), complex(F()), complex(I()))
    z = 3+4j
    print(complex(z) is z, {1+0j: 3}[1], 9007199254740992+0j == 9007199254740993)
    """,
]
CASES += [
    """
class Point:
    __match_args__ = ("x", "y")
    def __init__(self, x, y): self.x = x; self.y = y
class Color:
    RED = 1
    GREEN = 2
def describe(v):
    match v:
        case None: return "none"
        case True: return "true"
        case 0 | 1 as small: return f"small {small}"
        case -3.5: return "neg float"
        case 1+2j: return "complex"
        case "hi" | b"hi": return "greeting"
        case Color.RED: return "red"
        case Point(0, 0): return "origin"
        case Point(x=0, y=y): return f"y-axis {y}"
        case Point(x, y) if x == y: return f"diag {x}"
        case Point(): return "point"
        case [x, y, *rest]: return f"seq {x} {y} {rest}"
        case [x]: return f"one {x}"
        case (): return "empty"
        case {"k": v, **kw}: return f"map {v} {kw}"
        case {}: return "anymap"
        case int(n) if n > 100: return f"big {n}"
        case str() as s: return f"str {s}"
        case float(f): return f"float {f}"
        case _: return "other"
for v in [None, True, 0, 1, False, -3.5, 1+2j, "hi", b"hi", Color.RED, 2, Point(0, 0), Point(0, 5), Point(3, 3), Point(1, 2),
          [1, 2], [1, 2, 3, 4], (9,), [], (), {"k": 1, "z": 2}, {"a": 1}, 500, "s", 2.5, range(3), "ab", b"x", bytearray(b"ab")]:
    print(describe(v))
match [1, [2, 3]]:
    case [a, [b, *c]]:
        print(a, b, c)
x = 5
match x:
    case 1: pass
    case y: print("captured", y)
def gen(items):
    for item in items:
        match item:
            case [k, v] if (yield k):
                yield ("guard", v)
            case [k, v]:
                yield ("plain", k, v)
            case _:
                yield "skip"
g = gen([[1, 2], 3, [4, 5]])
print(next(g), g.send(True), next(g), next(g), g.send(False))
for bad in ["match x:\\n case _: pass\\n case 1: pass", "match x:\\n case a | b: pass", "match x:\\n case [a, a]: pass",
            "match x:\\n case {**_}: pass", "match x:\\n case [*a, *b]: pass", "match x:\\n case 1 + 2: pass",
            "match x:\\n case a: pass\\n case 2: pass", "match x:\\n case Point(x=1, x=2): pass"]:
    try: compile(bad, "<s>", "exec"); print("ok")
    except SyntaxError as e: print("SyntaxError", e.msg)
class C:
    __match_args__ = ("a",)
    a = 1
for code in ["match 1:\\n case int(1, 2): pass", "match C():\\n case C(1, 2): pass", "match 1:\\n case len(): pass", "match {'a':1}:\\n case {'a': 1, 'a': 2}: pass"]:
    try: exec(code); print("ok")
    except Exception as e: print(type(e).__name__, e)
match = 3; case = 4; print(match, case)
def f(match): return match
print(f(2), [match for match in [7]])
match = {"a": 1}
match["a"] = 2
print(match)
""",
    """
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
""",
]

CASES += [
    """
class D(dict):
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
""",
    """
class L(list):
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
""",
    """
a = {1}; b = a; a |= {2}; print(b, a is b)
x = [1]; y = x; x *= 2; print(y)
d = {1: 2}; e = d; d |= {3: 4}; print(e)
ba = bytearray(b"a"); bb = ba; ba += b"b"; print(bb)
class L(list): pass
l = L([1]); m = l; l *= 3; print(m, type(l).__name__)
class S(set): pass
s = S([1]); t = s; s |= {5}; print(sorted(t), type(s).__name__)
class D(dict): pass
q = D(a=1); r = q; q |= {"b": 2}; print(r, type(q).__name__)
class MyInt(int): pass
i = MyInt(3); i += 1; print(i, type(i).__name__)
class T(tuple): pass
print(T([1, 2]) + T([3]), T() == (), T("ab"), type(T("ab")[0:1]).__name__)
class Str(str):
    def __str__(self): return "custom"
print(str(Str("x")), repr(Str("x")), f"{Str('x')}", "%s" % Str("x"), Str("x") + "y")
class R(int):
    def __repr__(self): return "R!"
print(str(R(1)), repr(R(1)), f"{R(1)}", [R(1)])
class Init(list):
    def __init__(self, n):
        super().__init__(range(n))
        self.n = n
v = Init(3); print(v, v.n, v.__dict__, len(v))
class Slots(list):
    pass
w = Slots(); w.extra = 1; print(w, w.extra, vars(w))
print(MyInt.__base__, issubclass(MyInt, int), MyInt(5).__class__.__name__, type(MyInt(5)) is MyInt)
class N(int):
    def __new__(cls, v): return super().__new__(cls, v * 10)
print(N(4), N(4) + 0)
class K(dict):
    def __getitem__(self, k): return "over"
k = K(a=1); print(k["a"], k.get("a"), dict(k), list(k))
class Keyed(dict):
    def keys(self): return ["a"]
print(dict(Keyed(a=1, b=2)))
print(sorted([MyInt(3), 1, MyInt(2)]), max(MyInt(3), 9), sum([MyInt(1), MyInt(2)]))
print(MyInt(3) in {3}, Str("x") in {"x": 1}, {MyInt(3): "a"}, MyInt(10) // 3, MyInt(10) / 4, MyInt(2) ** 10, 5 - MyInt(2), [1] * MyInt(2))
""",
]

CASES.append("""
class Meta(type):
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
print(type(B) is Meta, B.tag, B.describe(), B.__mro__ == (B, A, object))
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
print(list(Color), len(Color), "RED" in Color, Color["GREEN"], repr(Color), str(Color), bool(Color), [Color])
class Check(type):
    def __instancecheck__(cls, obj): return obj == 42
    def __subclasscheck__(cls, sub): return sub is int
class Answer(metaclass=Check): pass
print(isinstance(42, Answer), isinstance(1, Answer), issubclass(int, Answer), issubclass(str, Answer), isinstance(Answer(), Answer))
def factory(name, bases, ns):
    return f"made {name} {sorted(k for k in ns if not k.startswith('__'))}"
class F(metaclass=factory):
    z = 3
print(F)
class M1(type): pass
class M2(type): pass
class P(metaclass=M1): pass
class Q(metaclass=M2): pass
try:
    class R(P, Q): pass
except TypeError as e: print("TypeError", e)
class M3(M1): pass
class S(P, metaclass=M3): pass
print(type(S).__name__)
class T(S): pass
print(type(T).__name__)
X = Meta("X", (), {"q": 5})
print(type(X).__name__, X.q, X.tag)
Y = type("Y", (A,), {})
print(type(Y).__name__, Y.tag)
class Attr(type):
    @property
    def area(cls): return "meta-prop"
    shared = "meta-attr"
class W(metaclass=Attr):
    shared = "class-attr"
print(W.area, W.shared, hasattr(W(), "area"))
print(type(Meta), type(type), Meta.__mro__, A.mro())
class Ops(type):
    def __or__(cls, other): return (cls.__name__, other.__name__)
    def __eq__(cls, other): return "eq"
    __hash__ = type.__hash__ if hasattr(type, "__hash__") else None
class O1(metaclass=Ops): pass
class O2(metaclass=Ops): pass
print(O1 | O2, O1 == O2)
class Sub(metaclass=Meta, extra=9):
    pass
class Init(type):
    def __init_subclass__(cls, **kw): print("meta subclass", cls.__name__)
class Init2(Init): pass
class Base:
    def __init_subclass__(cls, **kw):
        print("init_subclass", cls.__name__, kw)
class Child(Base, metaclass=M1, k=1): pass
""")

CASES += [
    """
def run(f):
    try: f()
    except BaseException as e: print(type(e).__name__, repr(e), getattr(e, "exceptions", None))
def a():
    try: raise TypeError(1)
    except* ValueError: pass
def b():
    try: raise ValueError(1)
    except* ValueError: raise
def c():
    try: raise ValueError(1)
    except* ValueError as e: print("caught", repr(e)); raise KeyError(2)
def d():
    try: raise ExceptionGroup("g", [ValueError(1), TypeError(2), ExceptionGroup("n", [ValueError(3), KeyError(4)])])
    except* ValueError as e: print("v", repr(e))
    except* KeyError as e: print("k", repr(e)); raise
def e():
    try: raise ExceptionGroup("g", [ValueError(1), TypeError(2)])
    except* ValueError: raise RuntimeError("new")
    except* TypeError: pass
for f in [a, b, c, d, e]: run(f)
eg = ExceptionGroup("m", [ValueError(1), TypeError(2)])
print(str(eg), eg.message, eg.exceptions, eg.args, repr(eg.split(ValueError)), repr(eg.subgroup(lambda x: isinstance(x, TypeError))))
print(type(BaseExceptionGroup("x", [ValueError()])).__name__, type(BaseExceptionGroup("x", [KeyboardInterrupt()])).__name__)
for bad in [lambda: ExceptionGroup("x", []), lambda: ExceptionGroup(1, [ValueError()]), lambda: ExceptionGroup("x", [1]), lambda: ExceptionGroup("x", [KeyboardInterrupt()]), lambda: ExceptionGroup("x"), lambda: ExceptionGroup("x", 5)]:
    try: bad()
    except TypeError as err: print("TypeError", err)
    except ValueError as err: print("ValueError", err)
""",
    """
for code in ["try: pass\\nexcept* ValueError: pass\\nexcept TypeError: pass", "try: pass\\nexcept*: pass",
             "def f():\\n    try: pass\\n    except* ValueError: return 1", "for i in []:\\n    try: pass\\n    except* ValueError: break",
             "for i in []:\\n    try: pass\\n    except* ValueError:\\n        for j in []: break", "try: pass\\nexcept* ValueError:\\n    def g(): return 1",
             "try: pass\\nexcept ValueError, TypeError as e: pass", "try: pass\\nexcept ValueError, TypeError: pass",
             "while True:\\n    try: pass\\n    except* ValueError: continue"]:
    try: compile(code, "<s>", "exec"); print("ok")
    except SyntaxError as e: print("SyntaxError", e.msg)
try:
    1 / 0
except ValueError, ZeroDivisionError:
    print("pep758")
def flow(exc):
    log = []
    try:
        try:
            if exc: raise exc
        except* ValueError as e:
            log.append(("v", repr(e)))
        except* (TypeError, KeyError) as e:
            log.append(("tk", repr(e)))
        else:
            log.append("else")
        finally:
            log.append("finally")
    except BaseException as outer:
        log.append(("outer", repr(outer)))
    return log
for exc in [None, ValueError(1), ExceptionGroup("g", [TypeError(1), KeyError(2), OSError(3)]), OSError(9)]:
    print(flow(exc))
try:
    try: raise ExceptionGroup("g", [ValueError(1)])
    except* ExceptionGroup: pass
except TypeError as e: print("TypeError", e)
try:
    try: raise ValueError
    except* 5: pass
except TypeError as e: print("TypeError", e)
class MyEG(ExceptionGroup):
    def derive(self, excs): return MyEG(self.message + "!", excs)
e = MyEG("m", [ValueError(1), TypeError(2)])
e.add_note("note")
m, r = e.split(ValueError)
print(type(m).__name__, m.message, m.__notes__, r.__notes__, m.__notes__ is e.__notes__)
print(e.subgroup((TypeError, KeyError)), e.subgroup(lambda x: False), e.split(BaseException))
try: e.split(5)
except TypeError as err: print(err)
try:
    try: raise MyEG("x", [ValueError(1), TypeError(2)])
    except* ValueError: pass
except ExceptionGroup as g: print(type(g).__name__, repr(g))
eg = BaseExceptionGroup("b", [KeyboardInterrupt(), ValueError()])
print(repr(eg), isinstance(eg, Exception), isinstance(ExceptionGroup("x", [ValueError()]), Exception))
print(issubclass(ExceptionGroup, BaseExceptionGroup), ExceptionGroup.__mro__)
print(str(ExceptionGroup("one", [ValueError()])), ExceptionGroup("x", (ValueError(),)).args)
def nested():
    try:
        try: raise ExceptionGroup("a", [ValueError(1), TypeError(2)])
        except* ValueError: raise KeyError("k")
    except* KeyError as e: print("caught", repr(e))
    except* TypeError as e: print("rest", repr(e))
nested()
try:
    try: raise ExceptionGroup("g", [ValueError(1)])
    except* ValueError as e: raise e
except ExceptionGroup as g: print("raise e", repr(g))
print(issubclass(FileNotFoundError, OSError), IOError is OSError, issubclass(UserWarning, Warning), TimeoutError.__mro__[1].__name__)
""",
    """
def gen(exc):
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
""",
]

# PEP 585 generic aliases, PEP 604 unions, and PEP 695 type parameters.
CASES += [
    """
print(list[int], dict[str, list[int]], tuple[int, ...], tuple[()], type[int], set[bytes], frozenset[int])
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
""",
    """
print(int | str, int | None, None | int, int | int, int | str | int, type(int | str))
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
""",
    """
def f[T: int, *Ts, **P, U: (int, str) = str](): pass
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
""",
    r"""
for src in ["def f[T, T](): pass", "def f[](): pass", "def f[T = int, U](): pass", "def f[*Ts: int](): pass",
            "def f[**P: int](): pass", "type X[T, T] = int", "class C[T: (int,)]: pass", "type = 5\nprint(type)",
            "type X = (yield)", "def f[T: (yield)](): pass", "def f[T](x=T): pass\nf()"]:
    try:
        exec(src, {})
        print("ok", repr(src))
    except (SyntaxError, NameError) as e:
        print(type(e).__name__, e.msg if isinstance(e, SyntaxError) else e)
type = 3
print(type)
del type
print(type(1))
class A:
    x = 1
    type T = x
    def m[U](self): return x
print(A.T.__value__)
x = "g"
print(A().m())
def f():
    class B[T]:
        def g(self): return T
    return B
B = f()
print(B.__qualname__, B.g.__qualname__, B().g())
class K[T, *Ts, **P]: pass
print(K.__type_params__, K[int, str, [int]], K[int, [bytes]])
try: K[int]
except TypeError as e: print(e)
class W[T = int]: pass
print(W[()] if False else W.__type_params__[0].__default__, W[str])
from_alias = list[int] | None
print(from_alias, from_alias.__args__)
type Deep[T] = list[T] | dict[str, T]
print(Deep[int], Deep.__value__, Deep[int].__args__, Deep.__parameters__)
def gen[T](x: T) -> T:
    yield x
print(next(gen(5)), gen.__type_params__)
async def co[T](): return 1
print(co.__type_params__)
lam = [lambda: T for T in [1]]
def nested[T]():
    def inner[U](): return (T, U)
    return inner
print(nested()(), nested().__qualname__, nested().__type_params__)
""",
]
# Numeric strings: Unicode digits and spaces, PEP 515 underscores, CPython errors.
CASES.append(r"""
for s in ["1_0.5", "1__0", "_1.0", "1.0_", "0x1p3", "  inf ", "-Infinity", "nAn", "1e5", "1e_5", ".5", "5.", "1_0e1_0", "  1.5 ", "+.e1", "", " ", "1e", "e1", "-.5e-3", "1.5j", "١.٥", "infinit", "+nan", "1\x00", "١٢"]:
    try: print(repr(s), float(s))
    except ValueError as e: print(e)
for s, b in [("12a", 10), (" 1 2", 10), ("١x", 10), ("", 10), ("0x1g", 0), ("z", 16), ("١_٢", 10), ("  7  ", 10), ("１２", 16), ("x" * 300, 10), ("0b101", 0), ("1_000", 10)]:
    try: print(repr(s)[:20], int(s, b))
    except ValueError as e: print(e)
try: int(b"z")
except ValueError as e: print(e)
print(complex("١+2j"), complex(" (1+2j) "), float(b"1.5"), int(b" 12 "))
""")
# Builtin method descriptors, slot wrappers, and their reprs.
CASES.append(r"""
def clean(s):
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
""")

# Live dictionary views and their set operations.
CASES.append(r"""
d = {'eggs': 2, 'sausage': 1, 'bacon': 1, 'spam': 500}
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
""")

# Builtin method types: method_descriptor, wrapper_descriptor, method-wrapper.
CASES.append(r"""
def clean(s):
    out = ""; i = 0
    while i < len(s):
        if s.startswith("0x", i):
            i += 2
            while i < len(s) and s[i] in "0123456789abcdef": i += 1
            out += "ADDR"
        else:
            out += s[i]; i += 1
    return out
for x in [list.append, [].append, int.__add__, (1).__add__, dict.fromkeys, object.__init__, object.__new__, int.__new__, list.__getitem__, [].__getitem__,
          dict.__contains__, {}.__contains__, set.__contains__, list.__contains__, int.__round__, (1).__round__, object.__format__, str.upper, "a".upper,
          list.__reversed__, float.__floor__, object.__repr__, object().__repr__, print, len, int.__init_subclass__, list.__class_getitem__]:
    print(type(x).__name__, clean(repr(x)))
print(type(list.append) is type(str.upper), type(list.append).__module__, type(int.__add__))
try: type(list.append)()
except TypeError as e: print(e)
""")

# object.__subclasshook__ defaults to NotImplemented.
CASES.append(r"""
print(object.__subclasshook__(int), int.__subclasshook__(1), type(object.__subclasshook__).__name__)
class A:
    @classmethod
    def __subclasshook__(cls, C): return True
print(A.__subclasshook__(int), issubclass(int, A))
for args in [(), (1, 2)]:
    try: object.__subclasshook__(*args)
    except TypeError as e: print(e)
try: object.__subclasshook__(x=1)
except TypeError as e: print(e)
""")

# Iterator classes, builtin iterator types, iter(callable, sentinel), zip strict.
CASES.append(r"""
for x in [iter([]), iter(()), iter(""), iter("é"), iter({}), iter(set()), iter(frozenset()), iter(range(1)), iter(range(2**70)), iter(b""), iter(bytearray()),
          map(abs, []), zip(), enumerate([]), reversed([]), reversed((1,)), reversed("ab"), filter(None, []), iter({}.items()), iter({}.values()), iter({}.keys()),
          reversed({}), reversed({}.values()), reversed({}.items()), iter(lambda: 1, 2), reversed(range(3)), iter(t"a{1}")]:
    print(type(x).__name__, type(x) is type(x), type(x).__module__)
print(type(map) is type, isinstance(map(abs, []), map), isinstance(zip(), zip), isinstance(enumerate([]), enumerate), isinstance(reversed([]), reversed), isinstance(filter(None, []), filter))
print(map, zip, list(map(abs, [-1, 2])), list(zip("ab", [1, 2], strict=True)), list(enumerate("ab", start=1)), list(filter(None, [0, 1])), list(reversed("ab")))
it = iter([1, 2, 3])
print(it.__next__(), next(it), it.__iter__() is it, type(it).__next__(it))
try: it.__next__()
except StopIteration: print("stop")
m = map(str, [1]); print(m.__next__(), iter(m) is m, map.__next__)
try: type(iter([])).__next__(iter(()))
except TypeError as e: print(e)
try: type(iter([]))()
except TypeError as e: print(e)
try: map()
except TypeError as e: print(e)
try: iter(1, 2)
except TypeError as e: print(e)
n = [0]
def counter():
    n[0] += 1
    return n[0]
print(list(iter(counter, 4)))
def raiser():
    raise StopIteration
print(list(iter(raiser, 0)))
ci = iter(counter, 8); print(next(ci), next(ci), list(ci), list(ci))
lines = iter(["a", "b", "", "c"]).__next__
print(list(iter(lines, "")))
for kw in [dict(start=2), dict(iterable='ab'), dict(iterable='ab', start=3), dict(start=3, iterable='ab'), dict(x=1)]:
    try: print(list(enumerate(**kw)))
    except TypeError as e: print(e)
for call in [lambda: enumerate('a', 1, start=2), lambda: enumerate('a', start='x'), lambda: enumerate(), lambda: zip(x=1)]:
    try: print(list(call()))
    except TypeError as e: print(e)
for a in [([1], [1, 2]), ([1, 2], [1]), ([1], [1], [1, 2]), ([1, 2], [1, 2], [1]), ([], []), ((), "", [])]:
    try: print(list(zip(*a, strict=True)))
    except ValueError as e: print(e)
print(list(zip([1], [1, 2], strict=False)), list(enumerate("ab", 5)))
for f, a in [(reversed, ()), (reversed, (1, 2)), (map, (abs,)), (enumerate, (1, 2, 3)), (filter, ()), (filter, (1, 2, 3)), (iter, ()), (iter, (1, 2, 3))]:
    try: f(*a)
    except TypeError as e: print(e)
""")

# printf-style formatting for str, bytes, and bytearray.
CASES.append(r"""
class I:
    def __index__(self): return 5
    def __repr__(self): return 'I()'
class F:
    def __float__(self): return 2.5
class N:
    def __int__(self): return 7
class B:
    def __bytes__(self): return b"BB"
class Bad:
    def __bytes__(self): return "x"
class M:
    def __getitem__(self, k): return k * 2
    def __repr__(self): return 'M()'
tests = [("%5.2f|%-4d|%x|%o|%e|%c|%r|%a|%%", (3.14159, 7, 255, 8, 12345.678, 65, "q", "é")), ("%(a)s-%(b)03d", {"a": 1, "b": 2}),
         ("%+d % d %#x %#o %05.1f %.3s %*d", (5, 5, 255, 8, 2.25, "abcdef", 4, 7)),
         ("%d", "x"), ("%x", 1.5), ("%f", "x"), ("%c", "ab"), ("%c", 0x110000), ("%c", 1.5), ("%*d", ("x", 1)), ("%(a)s", 1), ("%(a", {"a": 1}), ("%y", 1), ("%", 1), ("%s %s", (1,)), ("%s", (1, 2)), ("%(a)s", {}), ("%.*f", (2, 1.2345)), ("%s", {"a": 1}), ("%(a)s %s", {"a": 1}),
         ("%.3d|%-6.3x|%06.2f|%-06d|%+.2e|% d|%#.3o", (5, 255, 3.14159, 7, 1234.5, 3, 8)),
         ("%s", ()), ("%d", True), ("%i", 3.99), ("%x", True), ("%5c|%-3c|", ("x", 65)), ("%.1s %r %a", ("hello", "é", "é")), ("%#g %g %G %E", (1.0, 1e20, 1e-20, 2.0)), ("%010.3f|%-10.1f|%+010d", (-3.14159, 2.5, 42)), ("%%%s", "x"), ("%d", 10**30), ("%x", -(10**20)), ("%(x)s %(x)s", {"x": 1}),
         ("%ld %5.1lf", (1, 2.25)), ("%s", None), ("%r", [1, "a"]), ("%.0f %.0e", (0.5, 1.5)), ("%-+5d|", 3), ("%*.*f|", (8, 2, 3.14159)), ("%-*d|", (4, 1)), ("%*d|", (-4, 1)),
         ("%s %d", (1, "x")), ("%(a)d", {"a": "x"}), ("%s %s", 1), ("", 1), ("x", (1,)), ("", ()), ("", {}), ("%s", [1]), ("%(a)s", [1]), ("%s %*d", (1, 2.5, 3)), ("%.*d", ("q", 1)), ("%c", -1), ("%(a)c", {"a": "xy"}), ("%z", 1), ("%5", 1), ("abc %", ()), ("%(a)*d", {"a": 1}), ("%s", "x"), ("%d %s", ([], 1)), ("%c", 1.0),
         ("%d", I()), ("%x", I()), ("%f", I()), ("%f", F()), ("%d", F()), ("%d", N()), ("%x", N()), ("%c", I()), ("%s", M()), ("%(ab)s", M()),
         ("%s %(a)s", {"a": 1}), ("%(a)s %%", {"a": 1}), ("%-(a)5s|", {"a": 1}), ("%(a)-5s|", {"a": 1}), ("%(a)s", (1,)), ("%(a)s", "x"), ("%(a)s %(b)s", {"a": 1}), ("%s", b"x"), ("%5.1z", 1), ("%(a)", {"a": 1}), ("%(a)5", {"a": 1}), ("é%y", 1), ("%c", "é"), ("%10.4r|", "abcdef"), ("%x", 3.0), ("%.2147483648f", 1.0), ("%c", True), ("%#x %#X %#o", (0, 0, 0)), ("%e", 10**400),
         ("%!", 1), ("%'", 1), ("%é", 1), ("%\x01", 1), ("%5.2s|%-5.2s|%05s|", ("abc", "abc", "ab")), ("%#5x|%#-6X|%#06o|% #x", (255, 255, 8, 15)), ("%+.3d|% 05d|%-+08.3f", (-5, -3, 2.5)), ("%f %F %e", (float("inf"), float("nan"), float("-inf"))), ("%s%s", ("é", "ü")), ("%-4s|%4s|", ("é", "ü")), ("%r", "x" * 3), ("%((a))s", {"(a)": 1}), ("%s", I())]
for fmt, args in tests:
    try: print(repr(fmt % args))
    except Exception as e: print(type(e).__name__, e)
btests = [(b"%d-%s", (1, b"x")), (b"%s", "x"), (b"%c%c", (65, b"b")), (b"%r %a", ("é", "é")), (b"%5.1f|%x", (2.25, 255)), (b"%s", bytearray(b"z")), (b"%b", b"q"), (b"%c", 256), (b"%c", b"ab"), (b"%c", bytearray(b"ab")), (b"%c", "a"),
          (b"%s", B()), (b"%s", Bad()), (b"%(a)s", {b"a": b"v"}), (b"%(a)s", {"a": 1}), (b"%s", (1, 2)), (b"%s", [b"x"]), (b"%y", 1), (b"%\x01", 1), (b"%5s|%-5b|", (b"ab", b"cd")), (b"%.1s|%.2a", (b"xyz", "abc")), (b"%5c|", 65), (b"%(a)s", b"x"), (b"%d %d", 1)]
for fmt, args in btests:
    try: print(repr(fmt % args))
    except Exception as e: print(type(e).__name__, e)
print(repr(bytearray(b"%d!") % 5), type(bytearray(b"%s") % b"x").__name__)
class S(str):
    def __rmod__(self, other): return "rmod"
print("%s" % S("x"), "abc" % (), "%s" % (S("y"),))
""")

# Sequence subscript diagnostics.
CASES.append(r"""
for v in [[1], (1,), 'a', b'a', bytearray(b'a'), range(1)]:
    for k in [5, "x", 1.5]:
        try: v[k]
        except (IndexError, TypeError) as e: print(type(e).__name__, e)
for v in [[1], bytearray(b'a')]:
    for k in [5, "x"]:
        try: v[k] = 1
        except (IndexError, TypeError) as e: print(type(e).__name__, e)
        try: del v[k]
        except (IndexError, TypeError) as e: print(type(e).__name__, e)
""")

CASES.append(r"""
nan = float('nan'); inf = float('inf')
class MyInt(int): pass
for v, s in [(-nan, '+.2e'), (inf, '+F'), (-0.0, ''), (1e16, '.20'), (123.0, '.2'), (100.0, '#.3'),
             (1.5, '#.0f'), (1.5, '#g'), (-0.0001, 'z.2f'), (-0.0, 'z.3g'), (1, '٣'), (12345678, '_'),
             (0xdeadbeef, '_x'), (1234.56789, ',.2f'), (1234.56789, ',._f'), (-12345, '010,'), (12345, '=+12,'),
             (1234, '^11,'), (1 + 2j, '.2f'), (-0.0 + 1j, ''), (complex(-0.0, -0.0), ''), (1 + 1j, '^15.3e'),
             (65, 'c'), (97, '05c'), (255, '#X'), (255, '#012_b'), (3.5, '%'), (1e100, 'n'), (12345, 'n'),
             (-2**70, '_x'), (True, 'x'), (MyInt(7), '03'), ('héllo', '*^9.3'), (3, '€^9'), (1234567.891, '020_.3_f')]:
    print(repr(format(v, s)))
for v, s in [('abc', '+'), ('abc', ' '), ('abc', 'z'), ('abc', '#'), ('abc', '='), ('abc', 'd'), (5, '.2'), (5, 'z'),
             (97, '+c'), (97, '#c'), (0x110000, 'c'), (5, ',_'), (5, '_,'), (5, ',x'), (5, '.'), (5, 'xx'),
             (1.0, 'd'), (1j, '%'), (1j, '010'), (1j, '=10'), (None, 'x'), (5, 'n_'), (1.0, '.,_f'), (5, '9' * 30),
             (5, '\x01'), (1.0, '.2n,'), (MyInt(1), 'q')]:
    try: format(v, s)
    except (ValueError, TypeError, OverflowError) as e: print(type(e).__name__, e)
print(f"{1234567:,} {3.14159:_.2f} {'x':*>4} {97:c}")
""")

CASES.append(r"""
class P:
    x = 3
    def __format__(self, spec): return 'P' + spec
class D(dict):
    def __missing__(self, key): return key.upper()
print("{0[1]} {1.real} {a[k]} {a[0]}".format([5, 6], 2 + 3j, a={'k': 'v', 0: 'z'}))
print("{0:{1}{2}}|{0.x}|{1!r:>5}".format(P(), 'a', 'b'))
print("{:{w}.{p}f}".format(3.14159, w=10, p=2), "{0[١]}".format('xy'), "{a}{b}".format_map(D(a=1)))
for t in ["{0}{}", "{}{1}", "{0[}", "{0.}", "{0]}", "{", "}", "{0!x}", "{0!}", "{0:{1:{2}}}", "{5}", "{a}",
          "{0[2]}", "{0[0]x}", "{0!r", "{0!rx}", "{0[0}", "{a{}", "{0:>{1}}"]:
    try: t.format([1], 'a', 3)
    except (ValueError, KeyError, IndexError, TypeError) as e: print(type(e).__name__, e)
try: "{0}".format_map({})
except ValueError as e: print(e)
""")

CASES.append(r"""
for src in ["ub''", "turf''", "brft''", "def foo(/,a,b=,c):\n   pass", "def foo(a,/,/,b,c):\n   pass",
            "def foo(a,*b,c,/,d,e):\n   pass", "def foo(a,*b: int=,c):\n   pass", "def foo(a,**b: int=3):\n   pass",
            "def foo(a,*a, b, **c, *d):\n   pass", "def foo(a,b,/,c,*b,c,*d,**e):\n   pass", "def foo(a=1,/*,b,c):\n   pass",
            "def foo(a,d: int=,c):\n   pass", "lambda a=1,/,**b,/,c: None", "lambda (x, y, z), w: None",
            "def f((x, y, z, w)):\n   pass", "def f(*): pass", "lambda *, **k: 0", "def f(a=1, b): pass",
            "def f(a, *, a): pass", "def f(a:): pass", "def f(/): pass", "a = [1, 42 if True, 4]", "x = 1 if 1 else pass",
            "f(]", "f(\n]", "x = {\n1: 2", ")", "break", "continue", "async with x: pass", "yield from x", "await x",
            "def f(): await x", "def f(): [await x for x in y]", "break\nx = (", "while x:\n def f(): break",
            "async for x in range(10):\npass", "for x in range(10):\n    pass\nelse:\npass",
            "try:\n    something()\nexcept* A:\npass", "with (A as a, B as b):\npass", "class Blech[T](A):\npass",
            "match something:\n    case []:\n        ...\n    case {}:\npass", "def foo[T](x, /, y, *, z=2):\npass"]:
    try: compile(src, "<s>", "exec")
    except SyntaxError as e: print(type(e).__name__, e.msg, e.lineno)
""")

CASES += [r"""
from collections import *
import weakref, types
def t(f):
    try: r = f()
    except Exception as e: r = f'{type(e).__name__}: {e}'
    print(r)
d = deque('abcde')
t(lambda: d.index('c')); t(lambda: d.count('a')); t(lambda: 'q' in d); t(lambda: d * 2); t(lambda: 2 * d)
d.insert(1, 'X'); d.remove('c'); t(lambda: d); del d[0]; t(lambda: d); d[0] = 'Z'; t(lambda: d)
d.reverse(); t(lambda: d); d.rotate(-1); t(lambda: d); d.extendleft('12'); t(lambda: d)
t(lambda: deque([1,2]) == deque([1,2])); t(lambda: deque([1]) <= deque([1, 0])); t(lambda: deque([3]) > deque([1]))
t(lambda: deque(range(3), maxlen=0)); t(lambda: deque(maxlen=2).maxlen); x = deque([1,2,3]); x += [4]; t(lambda: x)
x *= 0; t(lambda: x); t(lambda: deque([1]).copy()); t(lambda: bool(deque())); t(lambda: list(reversed(deque([1,2,3]))))
t(lambda: deque([1, 2])[-1]); t(lambda: deque([1, 2])[-3]); t(lambda: deque[int])
y = deque([1, 2, 3], 3); y.append(4); t(lambda: y); y.appendleft(0); t(lambda: y); y.extend([7, 8]); t(lambda: y)
t(lambda: deque([1, 2]) + deque([3])); t(lambda: deque().pop())
for i in range(100): y.appendleft(i)
t(lambda: (len(y), y[0], y[2]))
q = deque()
for i in range(50): q.append(i)
for i in range(45): q.popleft()
t(lambda: q)
dd = defaultdict(int)
for ch in 'mississippi': dd[ch] += 1
t(lambda: dd); t(lambda: dict(dd)); t(lambda: dd.copy()); t(lambda: dd == {'m': 1, 'i': 4, 's': 4, 'p': 2})
t(lambda: defaultdict(list, {1: 2}) | {3: 4}); t(lambda: {3: 4} | defaultdict(list, {1: 2})); t(lambda: defaultdict(lambda: 5)['k'] if False else defaultdict(None))
t(lambda: defaultdict(int).get('x')); t(lambda: 'x' in defaultdict(int)); t(lambda: defaultdict.__name__)
t(lambda: isinstance(defaultdict(), dict)); t(lambda: defaultdict(int, a=1, b=2))
od = OrderedDict.fromkeys('abc', 0); t(lambda: od); od['a'] = 5; t(lambda: list(od)); t(lambda: od.pop('b')); t(lambda: od.pop('b', 'dflt'))
t(lambda: od.setdefault('z', 9)); t(lambda: od); t(lambda: od == {'a': 5, 'c': 0, 'z': 9}); t(lambda: od | {'q': 1})
t(lambda: OrderedDict(a=1) == OrderedDict(a=1)); t(lambda: OrderedDict([('a', 1), ('b', 2)]) != OrderedDict([('b', 2), ('a', 1)]))
t(lambda: od.copy()); t(lambda: list(reversed(od))); t(lambda: od.popitem()); t(lambda: od)
P = namedtuple('Point', ['x', 'y'])
p = P(1, 2); t(lambda: p); t(lambda: P(x=3, y=4)); t(lambda: P._make([5, 6])); t(lambda: P.__doc__); t(lambda: p.x + p.y)
t(lambda: P(1)); t(lambda: P(1, 2, 3)); t(lambda: namedtuple('Bad', ['_a'])); t(lambda: namedtuple('Bad', ['a', 'a']))
t(lambda: namedtuple('Bad', 'class')); t(lambda: namedtuple('R', 'a _b a class', rename=True)._fields); t(lambda: isinstance(p, tuple))
t(lambda: p._replace(z=1)); t(lambda: P._field_defaults); t(lambda: hash(p) == hash((1, 2))); t(lambda: P.__match_args__)
t(lambda: P.x.__doc__); t(lambda: p.__getnewargs__())
match p:
    case P(x=1, y=yy): print('matched', yy)
c = Counter(a=3, b=1)
t(lambda: c.most_common()); t(lambda: c.most_common(1)); c.update('aab'); t(lambda: c); c.subtract({'a': 10}); t(lambda: c)
t(lambda: +c); t(lambda: -c); t(lambda: c | Counter(z=2)); t(lambda: c & Counter(b=1)); t(lambda: Counter('ab') ^ Counter('bc'))
t(lambda: Counter('aab') <= Counter('aabb')); t(lambda: Counter.fromkeys('a')); t(lambda: Counter() == Counter(a=0))
c2 = Counter('xy'); c2 += Counter('x'); t(lambda: c2); del c2['nope']; t(lambda: c2)
cm = ChainMap({'a': 1}, {'b': 2})
cm['c'] = 3; t(lambda: cm); t(lambda: cm.parents); t(lambda: cm.maps); t(lambda: 'b' in cm); t(lambda: cm.get('b'))
t(lambda: dict(cm)); t(lambda: cm.pop('c')); t(lambda: cm.pop('b')); t(lambda: cm | {'x': 1}); t(lambda: list(cm.keys()))
t(lambda: list(cm.items())); t(lambda: cm == {'a': 1, 'b': 2}); t(lambda: bool(ChainMap()))
ud = UserDict({'k': 1}); t(lambda: ud | {'j': 2}); t(lambda: ud.copy()); t(lambda: ud.pop('k')); t(lambda: ud); t(lambda: ud.setdefault('m', 3))
ul = UserList([3, 1, 2]); ul.sort(); t(lambda: ul); t(lambda: ul * 2); t(lambda: ul.index(2)); t(lambda: ul.count(1)); t(lambda: ul == [1, 2, 3])
ul.reverse(); t(lambda: ul); t(lambda: ul.pop()); t(lambda: ul); t(lambda: 3 in ul); t(lambda: ul[0])
us = UserString('abc'); t(lambda: us * 2); t(lambda: us.find('c')); t(lambda: us.split('b')); t(lambda: us == 'abc'); t(lambda: 'b' in us)
t(lambda: us.replace('a', 'z')); t(lambda: us.zfill(5)); t(lambda: us.join(['1', '2'])); t(lambda: us < 'b'); t(lambda: str(us))
ns = types.SimpleNamespace(x=1)
t(lambda: ns.__replace__(x=2)); t(lambda: types.SimpleNamespace(1, 2)); t(lambda: types.SimpleNamespace({1: 2}))
t(lambda: types.ModuleType()); t(lambda: types.ModuleType(1)); t(lambda: types.ModuleType('a', 'b', 'c'))
t(lambda: types.ModuleType(name='q')); t(lambda: types.MethodType(1, 2)); t(lambda: types.MethodType(len, None))
t(lambda: types.resolve_bases((int,))); t(lambda: types.prepare_class('A'))
t(lambda: types.get_original_bases(int)); t(lambda: types.FunctionType.__name__); t(lambda: types.SimpleNamespace.__module__)
class A: pass
a = A()
r = weakref.ref(a)
t(lambda: r == weakref.ref(a)); t(lambda: hash(r) == hash(a)); t(lambda: weakref.getweakrefcount(a)); t(lambda: weakref.getweakrefs(a) == [r])
t(lambda: weakref.ref(a, lambda x: None) == r); t(lambda: weakref.ref(1)); t(lambda: weakref.proxy(a) is weakref.proxy(a))
p = weakref.proxy(a); a.v = [1, 2]; t(lambda: p.v); t(lambda: len(p.v))
del a
t(lambda: r()); t(lambda: hash(r) is not None); t(lambda: p.v)
class B: pass
b = B(); r2 = weakref.ref(b); del b
t(lambda: hash(r2))
wd = weakref.WeakValueDictionary()
class V: pass
vs = [V() for i in range(3)]
for i, v in enumerate(vs): wd[i] = v
t(lambda: sorted(wd.keys())); del vs[1]; t(lambda: sorted(wd.keys())); t(lambda: 1 in wd); t(lambda: wd.get(1, 'gone'))
ws = weakref.WeakSet(vs); t(lambda: len(ws)); vs.pop(); t(lambda: len(ws))
f = weakref.finalize(vs[0], print, 'fin', 1); t(lambda: f.alive); t(lambda: f()); t(lambda: f.alive); t(lambda: f())
cp = weakref.proxy(len); t(lambda: cp([1, 2])); t(lambda: type(cp).__name__); t(lambda: callable(cp))
t(lambda: weakref.ref.__module__); t(lambda: weakref.ReferenceType.__name__); t(lambda: weakref.ref[int])
""", r"""
import weakref
class A: pass
a = A(); calls = []
r = weakref.ref(a, lambda wr: calls.append(wr))
print(r() is a, weakref.getweakrefcount(a), r.__callback__ is not None)
r2 = weakref.ref(a); print(r2 is weakref.ref(a), r2 is not r)
del a
print(r(), calls == [r], r2(), r.__callback__)
for o in (1, 'x', [], {}, len, Exception(), A, set(), object(), r2, (1,), b'', range(1)):
    try: weakref.ref(o); print(type(o).__name__, 'ok')
    except TypeError as e: print(e)
class S: __slots__ = ()
class T(S): pass
class U: __slots__ = ('__weakref__',)
class I(int): pass
for k in (S, T, U, I):
    try: weakref.ref(k()); print('ok')
    except TypeError as e: print(e)
k = weakref.WeakKeyDictionary(); y = A(); k[y] = 1; print(len(k)); del y; print(len(k))
class B:
    def m(self): return 5
b = B(); wm = weakref.WeakMethod(b.m); print(wm()()); del b; print(wm())
q = A(); f = weakref.finalize(q, print, 'finalized'); print(f.alive); del q
print('after', f.alive)
def boom(wr): raise ValueError('ignored')
z = A(); zr = weakref.ref(z, boom); del z
print('still running', zr())
order = []
z = A(); r1 = weakref.ref(z, lambda w: order.append(1)); r2 = weakref.ref(z, lambda w: order.append(2)); del z
print(order)
def gen():
    yield 1
g = gen(); gr = weakref.ref(g); del g; print(gr())
class L(list): pass
print(list(reversed(L([1, 2]))))
class Seq:
    def __len__(self): return 3
    def __getitem__(self, i): return i * 10
print(list(reversed(Seq())))
print(property(fget=len, doc='d').__doc__)
"""]

CASES.append(r"""
# property, classmethod and staticmethod subclasses.
x = property.__new__(property)
print(type(x), x.fget)
class P(property):
    "P doc"
class Q(property): pass
def g(self):
    "get doc"
    return 42
class C:
    a = P(g)
    b = Q(g, doc="explicit")
    @P
    def c(self): return 5
    @c.setter
    def c(self, v): print("set", v)
    cm = classmethod(lambda cls: cls.__name__)
print(C().a, C.a.__doc__, C.b.__doc__, type(C.c).__name__, C().c, vars(C.a))
C().c = 9
try: del C().c
except AttributeError as e: print(e)
class CM(classmethod):
    pass
class SM(staticmethod):
    pass
class D:
    @CM
    def f(cls, x): return (cls.__name__, x)
    @SM
    def h(x): return x * 2
print(D.f(1), D().f(2), D.h(3), D().h(4), repr(D.__dict__['f'])[:20], D.__dict__['h'].__func__.__name__)
print(vars(D.__dict__['f']).keys(), D.__dict__['h'](5), isinstance(D.__dict__['f'], classmethod))
""")

CASES.append(r"""
# property accessor errors name the property and owner.
class C:
    x = property(lambda s: 1)
    y = property()
    z = property(None, lambda s, v: None)
for f in [lambda: setattr(C(), "x", 1), lambda: delattr(C(), "x"), lambda: C().y, lambda: delattr(C(), "z"),
          lambda: property.__get__(C.x, None, None), lambda: C.x.__set__(C(), 1), lambda: classmethod(), lambda: staticmethod(1, 2)]:
    try: print(f())
    except Exception as e: print(type(e).__name__, e)
print(repr(classmethod(len)), repr(staticmethod(len)))
""")

CASES.append(r"""
# sys._getframe frames and their write-through FrameLocalsProxy (PEP 667).
import sys
f0 = sys._getframe()
print(type(f0).__name__, f0.f_globals is globals(), f0.f_locals is globals(), f0.f_back, f0.f_lineno)
print(f0.f_code.co_name if hasattr(f0.f_code, "co_name") else None)
def outer():
    a = 1
    def inner(x):
        b = a + x
        fr = sys._getframe()
        loc = fr.f_locals
        print(type(loc).__name__, sorted(loc.keys()), loc["x"], "a" in loc, len(loc), loc.get("zz", 7))
        loc["b"] = 10
        print(b)
        loc["new"] = 5
        print(sorted(loc), loc["new"], loc.pop("new"), "new" in loc)
        try: del loc["b"]
        except ValueError as e: print(e)
        try: loc["nope"]
        except KeyError as e: print(repr(e))
        try: loc.pop("b")
        except ValueError as e: print(e)
        print(loc == dict(loc), loc == loc, loc != {}, dict(loc) == loc.copy())
        print(fr.f_back.f_code.co_name, fr.f_back.f_back.f_back is None, sys._getframe(1) is fr.f_back)
        print(fr.f_lineno, fr.f_back.f_lineno)
        print(repr(loc)[:30])
        return fr
    return inner(2)
fr = outer()
print(fr.f_back.f_code.co_name, fr.f_lineno, sorted(fr.f_locals))
try: sys._getframe(99)
except ValueError as e: print(e)
class K:
    v = sys._getframe().f_locals
    print(v is locals(), sys._getframe().f_code.co_name)
def gen():
    yield sys._getframe().f_code.co_name
    yield sys._getframe().f_back.f_code.co_name
print(list(gen()))
x = (lambda: sys._getframe().f_locals)()
print(type(x).__name__, x | {"q": 1}, {"q": 1} | x)
def deep(n):
    return sys._getframe().f_back.f_locals["n"] if n == 0 else deep(n - 1)
print(deep(3))
""")

CASES.append(r"""
# sys._getframemodulename and the types module frame names.
import sys, types
def f(d=0): return sys._getframemodulename(d)
print(f(), f(1), f(50), sys._getframemodulename())
f.__module__ = "zz"
print(f(), types.FrameType.__name__, types.FrameLocalsProxyType.__name__)
try: sys._getframemodulename("x")
except TypeError as e: print(e)
""")

CASES.append(r"""
# type.__subclasses__ lists live direct subclasses in creation order.
class A: pass
class B(A): pass
class C(A): pass
class D(B, C): pass
print(A.__subclasses__(), B.__subclasses__(), D.__subclasses__())
del C
print([k.__name__ for k in A.__subclasses__()])
print(int.__subclasses__() == [bool] or int.__subclasses__())
""")

CASES.append(r"""
# sys recursion and integer-string limits, and PEP 810 lazy imports of built-in modules.
import sys
print(sys.getrecursionlimit(), sys.get_int_max_str_digits(), sys.version_info[:2], sys.maxsize == 2**63 - 1)
def down(n): return down(n + 1)
try: down(0)
except RecursionError as e: print(type(e).__name__, e)
old = sys.getrecursionlimit()
sys.setrecursionlimit(50)
def depth(n=1):
    try: return depth(n + 1)
    except RecursionError: return n
print(depth() <= 50)
sys.setrecursionlimit(old)
for bad in [0, -1, 2**40, "x"]:
    try: sys.setrecursionlimit(bad)
    except Exception as e: print(type(e).__name__, e)
for value in ["1" * 4301, "1" * 4300]:
    try: print(len(str(int(value))))
    except ValueError as e: print(e)
sys.set_int_max_str_digits(0)
print(len(str(10 ** 5000)))
sys.set_int_max_str_digits(5000)
try: str(10 ** 5000)
except ValueError as e: print(e)
for bad in [10, -1]:
    try: sys.set_int_max_str_digits(bad)
    except ValueError as e: print(e)
sys.set_int_max_str_digits(4300)
print(sys.float_info.max == 1.7976931348623157e+308, sys.float_info.dig, sys.int_info.default_max_str_digits)
print(float.__getformat__("double"), sys.intern("ab") is sys.intern("ab"))
try: type(sys.version_info)()
except TypeError as e: print(e)
print(sys.modules["sys"] is sys, sys.exc_info())
try: raise KeyError(1)
except KeyError: print(sys.exc_info()[0], sys.exception())
lazy import collections
lazy from weakref import ref as lazy_ref
print(type(globals()["collections"]).__name__, type(globals()["lazy_ref"]).__name__)
print(collections.deque([1, 2]), type(globals()["collections"]).__name__)
print(lazy_ref.__name__, globals()["lazy_ref"] is lazy_ref)
lazy import missing_module_for_lazy
try: missing_module_for_lazy
except ModuleNotFoundError as e: print(type(e).__name__, e, type(e.__cause__).__name__, e.__cause__)
for source in ["def f():\n    lazy import x", "class C:\n    lazy import x", "try:\n    lazy import x\nexcept: pass",
               "lazy from x import *", "lazy from __future__ import annotations", "from x lazy import y"]:
    try: compile(source, "<s>", "exec")
    except SyntaxError as e: print(e.msg, e.lineno)
lazy = 3
print(lazy)
""")

CASES.append(r"""
# CPython's error spans for range-based parser diagnostics and tokenizer errors.
for source in ["[1, 2 3]", "x = 1 +", "print 'x'", "import a.b from c.d", "case 1: pass", "match x\n  case 1: pass",
               "x = 08", "0x", "0o8", "1_000_", "1.5j_", "with a,: pass", "raise from x", "3 + not 3", "- not 3", "{1: 2, 3}",
               "{1:}", "f(x for x in y, 1)", "f(a, x for x in y if z)", "'a' b 'c'", "x = pass if 1 else 1", "[a b",
               "[a b c", "from t import x,", "import a as b.c", "try:\n  pass\nexcept E as a.b:\n  pass", "x = 'abc",
               "x = f'abc", "match x:\n  case 1 as a():\n    pass", "fur x in y:\n  pass", "class C(x for x in y): pass",
               "for x im y:\n  pass"]:
    try:
        compile(source, "<s>", "exec")
    except SyntaxError as e:
        print(type(e).__name__, e.msg, e.lineno, e.offset, e.end_lineno, e.end_offset)
namespace = {}
exec(compile('def g():\n    return f"{(yield 1)}"\n', "<s>", "exec"), namespace)
print(next(namespace["g"]()))
for source in ['x = f"{yield}"', 'x = f"{await y}"', 'x = (await\n  y)']:
    try: compile(source, "<s>", "exec")
    except SyntaxError as e: print(e.msg, e.lineno)
""")

CASES.append(r"""
extra = ['x = a < b = 1','x = f() = y = 1','x = 1 = 2','[1] + 2 = 3','(a) + 1 = 2','[x for x in y] = 1','x() = yield','x = f() = 1 if 2 else 3','-1 = 2','not a = 1','a, f() = 1','*a = 1','*a += 1','del *a','del (a, f())','if x == 1 = 2: pass','x = (yield) = 1','f() = 1 = 2','a.b, c() = 1','x = lambda: 1 = 2','await x = 1','(x = 1)','[a, b() = 1]','x = f() == 1 = 2','x = 1','a, b = 1, 2','x = y = z = 0','a[0], b.c = 1, 2','*a, b = c','[a, *b] = c','(a) = 1','x += 1','del a, b[0], c.d','for (a, b) in c: pass','with a as (b, c): pass','[x for (a, b) in y]','assert x == 1, "m"','assert (x := 1)','assert x := 1','assert 1, x := 2','f(a) = 1 = 2','a, *b() = 1','(a, b()) = 1','x = [y = 1]']
for src in ['None = 1', 'True = 1', '(True := 1)', 'f() = 1', 'yield = 1', 'del f()', 'a + 1 = 2', '1 = 1', '"abc" = 1', 'b"" = 1', '... = 1', '(a, "b", c) = (1, 2, 3)', '(a, True, c) = (1, 2, 3)', '(a, *True, c) = (1, 2, 3)', '[a, b, c + 1] = [1, 2, 3]', '[a, b[1], c + 1] = [1, 2, 3]', '[a, b.c.d, c + 1] = [1, 2, 3]', 'a if 1 else b = 1', 'True = True = 3', 'x = y = True = z = 3', 'x = y = yield = 1', 'a, b += 1, 2', '(a, b) += 1, 2', '[a, b] += 1, 2', 'for a() in b: pass', 'for (a, b()) in b: pass', 'for [a, b()] in b: pass', 'for (*a, b, c+1) in b: pass', 'for (x, *(y, z.d())) in b: pass', 'for a, b() in c: pass', 'for a, b, (c + 1, d()): pass', 'with a as b(): pass', 'with a as (b, c()): pass', 'with a as [b, c()]: pass', 'with a as (*b, c, d+1): pass', 'with a as (x, *(y, z.d())): pass', 'with a as b, c as d(): pass', '[x for x() in a]', '[x for a, b, (c + 1, d()) in y]', '[x for x+1 in y]', '[x for x+1, x() in y]', 'f(True=1)', 'f(False=1)', 'f(None=1)', 'f(*args=[0])', 'f(a, b, *args=[0])', "f(**kwargs={'a': 1})", "f(a, b, *args, **kwargs={'a': 1})", 'None += 1', 'f() += 1', 'if 1:\n  x() = 1\nelif 1:\n  pass', 'if 1:\n  pass\nelif 1:\n  x() = 1', 'if 1:\n  x() = 1\nelif 1:\n  pass\nelse:\n  pass', 'if 1:\n  pass\nelif 1:\n  x() = 1\nelse:\n  pass', 'if 1:\n  pass\nelif 1:\n  pass\nelse:\n  x() = 1', 'if x = 3:\n   pass', 'while x = 3:\n   pass', 'if x.a = 3:\n   pass', 'while x.a = 3:\n   pass', '{1, 2, 3} = 42', '{1: 2, 3: 4} = 42', "f'{x}' = 42", "f'{x}-{y}' = 42", "t'{x}' = 42", "t'{x}-{y}' = 42", '(x, y, z=3, d, e)', '[x, y, z=3, d, e]', '[z=3]', '{x, y, z=3, d, e}', '{z=3}', 'import a as b; None = 1', 'import a, b as c; d = 1; None = 1', 'from a import b as c; None = 1', 'from a import b, c as d; e = 1; None = 1', 'assert a := 1', 'assert 1, a := 1', 'assert 1 = 2 = 3', 'assert 1 = 2', 'assert (1 = 2)', "assert 'a' = a", 'assert x[0] = 1', 'assert (yield a) = 2', 'assert a = 2', 'assert (a = 2)', 'assert a = b', 'assert 1, 1 = b', 'assert 1, (1 = b)', 'assert 1, a = 1', 'assert 1, (a = 1)', 'assert 1 = a, a = 1'] + extra:
    try: compile(src, '<s>', 'exec'); print(repr(src), 'OK')
    except SyntaxError as e: print(repr(src), e.msg, e.lineno)
for src in ['A[*(1:2)]', 'A[*]', 'f(**x, *)', 'f(x = 5, *:)', 'f(**x, *y)', 'f(a=)', 'f((x)=2)', 'f(True=1)', "f(**kwargs={'a': 1})"]:
    try: compile(src, '<s>', 'exec')
    except SyntaxError as e: print(repr(src), e.msg)
""")

ERRORS = [
    ("len(range(10**100))", "OverflowError"),
    ("range(3)[10**100]", "IndexError"),
    ("range(3)[-10**100]", "IndexError"),
    ("range(10)[::0]", "ValueError"),
    ("range(10).index(20)", "ValueError"),
    ("slice(1).indices(-10**100)", "ValueError"),
    ("__import__('')", "ValueError"),
    ("__import__(42)", "TypeError"),
    ("__import__('x', level=-1)", "ValueError"),
    ("from x import (a,, b)", "SyntaxError"),
    ("from x import a,", "SyntaxError"),
    ("import x,", "SyntaxError"),
    ("def f():\n    from x import *", "SyntaxError"),
    ("from . import x", "ImportError"),
    ("[x async for x in a]", "SyntaxError"),
    ("def f():\n    return [x async for x in a]", "SyntaxError"),
    ("[await x for x in a]", "SyntaxError"),
    ("async def f():\n    return [await x for x in a]\nf().send(None)", "NameError"),
    ("aiter([])", "TypeError"),
    ("anext(iter([]))", "TypeError"),
    ("class A:\n    def __aiter__(self): return []\naiter(A())", "TypeError"),
    ("class A:\n    def __anext__(self): return 1\nnext(anext(A(), 2))", "TypeError"),
    ("async def f():\n    yield from []", "SyntaxError"),
    ("async def f():\n    yield 1\n    return 2", "SyntaxError"),
    ("async def f():\n    if False: yield 1\n    if True: return 2", "SyntaxError"),
    ("await x", "SyntaxError"),
    ("async def f():\n    def g():\n        return await x", "SyntaxError"),
    ("async def f():\n    return lambda: await x", "SyntaxError"),
    ("async def f():\n    return await -1", "SyntaxError"),
    ("async def f():\n    return await 1\nf().send(None)", "TypeError"),
    ("class A:\n    def __await__(self): return [1]\nasync def f():\n    return await A()\nf().send(None)", "TypeError"),
    ("async for x in []:\n    pass", "SyntaxError"),
    ("async def f():\n    async for x in []:\n        pass\nf().send(None)", "TypeError"),
    ("class A:\n    def __aiter__(self): return self\n    def __anext__(self): return 1\nasync def f():\n    async for x in A(): pass\nf().send(None)", "TypeError"),
    ("b'é'", "SyntaxError"),
    ("b'a' 'b'", "SyntaxError"),
    ("'a' b'b'", "SyntaxError"),
    ("b'\\x0'", "SyntaxError"),
    ("bytes([-1])", "ValueError"),
    ("bytes([256])", "ValueError"),
    ("bytes([2**100])", "ValueError"),
    ("bytes([1.0])", "TypeError"),
    ("bytes(-1)", "ValueError"),
    ("bytes('abc')", "TypeError"),
    ("b'a' + 'b'", "TypeError"),
    ("'a' + b'b'", "TypeError"),
    ("b'a'[0] = 2", "TypeError"),
    ("256 in b'abc'", "ValueError"),
    ("'a' in b'abc'", "TypeError"),
    ("1j / 0", "ZeroDivisionError"),
    ("0j ** -1", "ZeroDivisionError"),
    ("1j < 2j", "TypeError"),
    ("complex('1 + 2j')", "ValueError"),
    ("complex('1__2j')", "ValueError"),
    ("complex('1j', 2)", "TypeError"),
    ("class C:\n    def __complex__(self): return 1\ncomplex(C())", "TypeError"),
    ("bool(NotImplemented)", "TypeError"),
    ("1 @ 2", "TypeError"),
    ("f'{!r}'", "SyntaxError"),
    ("f'{1!q}'", "SyntaxError"),
    ("f'}'", "SyntaxError"),
    ("f'{1'", "SyntaxError"),
    ("class C:\n    def __format__(self, spec): return 1\nf'{C()}'", "TypeError"),
    ("format(1, '.2d')", "ValueError"),
    ("format('x', '+3')", "ValueError"),
    ("class C:\n    @property\n    def x(self): return 1\nc = C(); c.x = 2", "AttributeError"),
    ("class C:\n    @property\n    def x(self): return 1\nc = C(); del c.x", "AttributeError"),
    ("@1\ndef f(): pass", "TypeError"),
    ("'{missing}'.format(present=1)", "KeyError"),
    ("__debug__ = 1", "SyntaxError"),
    ("obj.__debug__ = 1", "SyntaxError"),
    ("del __debug__", "SyntaxError"),
    ("def f(__debug__): pass", "SyntaxError"),
    ("f(__debug__=1)", "SyntaxError"),
    ("nonlocal x", "SyntaxError"),
    ("def f():\n nonlocal missing", "SyntaxError"),
    ("def f(x):\n global x", "SyntaxError"),
    ("def f(x):\n nonlocal x", "SyntaxError"),
    ("def f():\n x=1\n global x", "SyntaxError"),
    ("def f():\n print(x)\n global x", "SyntaxError"),
    ("def f():\n x=1\n nonlocal x", "SyntaxError"),
    ("def f():\n global x\n nonlocal x", "SyntaxError"),
    ("def f():\n global x\n def g():\n  nonlocal x", "SyntaxError"),
    ("class C:\n x=1\n def f(self):\n  nonlocal x", "SyntaxError"),
    ("def f():\n global x\n x=1\n global x", "SyntaxError"),
    ("def f(): yield from [], []", "SyntaxError"),
    ("def f(): x = yield from [], []", "SyntaxError"),
    ("def f(): return yield 1", "SyntaxError"),
    ("def f(): yield yield 1", "SyntaxError"),
    ("def f(): print(yield 1)", "SyntaxError"),
    ("def f(): assert yield 1", "SyntaxError"),
    ("print(1, sep=1)", "TypeError"),
    ("print(1, end=1)", "TypeError"),
    ("print(1, nope=1)", "TypeError"),
    ("[1,2][::0]", "ValueError"),
    ("[1,2][1.5:]", "TypeError"),
    ("a = [1,2,3]; a[::2] = [0]", "ValueError"),
    ("a = [1,2]; a[:] = 1", "TypeError"),
    ("slice(1).start = 2", "AttributeError"),
    ("slice(1).indices(-1)", "ValueError"),
    ("yield 1", "SyntaxError"),
    ("yield from []", "SyntaxError"),
    ("def f(): return [(yield i) for i in []]", "SyntaxError"),
    ("def f(): return (i for i in [] if (yield 1))", "SyntaxError"),
    ("def f(): return {i: (yield i) for i in []}", "SyntaxError"),
    ("1 / 0", "ZeroDivisionError"),
    ("1 // 0", "ZeroDivisionError"),
    ("1 % 0", "ZeroDivisionError"),
    ("0 ** -1", "ZeroDivisionError"),
    ("missing", "NameError"),
    ("[1][2]", "IndexError"),
    ("{}['x']", "KeyError"),
    ("{}[[]]", "TypeError"),
    ("{[]: 1}", "TypeError"),
    ("1 + 'x'", "TypeError"),
    ("1(2)", "TypeError"),
    ("len(1)", "TypeError"),
    ("range(1, 2, 0)", "ValueError"),
    ("1 << -1", "ValueError"),
    ("[].pop()", "IndexError"),
    ("assert False, 'oops'", "AssertionError"),
    ("def f(a): return a\nf()", "TypeError"),
    ("x = 1\ndef f():\n    print(x)\n    x = 2\nf()", "UnboundLocalError"),
    ("def f():\n    if False:\n        x = 1\n    return x\nf()", "UnboundLocalError"),
    ("return 1", "SyntaxError"),
    ("break", "SyntaxError"),
    ("continue", "SyntaxError"),
    ("if:\n pass", "SyntaxError"),
    ("def f(a, a): pass", "SyntaxError"),
    ("(1]", "SyntaxError"),
    ("'unterminated", "SyntaxError"),
    ("1 = 2", "SyntaxError"),
    ("1e+", "SyntaxError"),
    ("1__0", "SyntaxError"),
    ("0123", "SyntaxError"),
    ("1_e2", "SyntaxError"),
    ("1e_2", "SyntaxError"),
    ("1 + not 2", "SyntaxError"),
    ("[] in {}", "TypeError"),
    ("(*x), y = 1, 2", "SyntaxError"),
    ("[x := 1 for x in range(3)]", "SyntaxError"),
    ("[x for x in (y := range(3))]", "SyntaxError"),
    ("class C:\n    x = [(y := 1) for z in range(3)]", "SyntaxError"),
    ("def f(a): pass\nf(1, a=2)", "TypeError"),
    ("def f(*, a): pass\nf(1)", "TypeError"),
    ("def f(a, /): pass\nf(a=1)", "TypeError"),
    ("def f(**kw): pass\nf(**{1: 2})", "TypeError"),
    ("def f(**kw): pass\nf(a=1, **{'a': 2})", "TypeError"),
    ("try:\n    pass\nelse:\n    pass", "SyntaxError"),
    ("try:\n    1 / 0\nexcept 42:\n    pass", "TypeError"),
    ("class C:\n    def __bool__(self): return 1\nbool(C())", "TypeError"),
    ("class C:\n    def __str__(self): return 1\nstr(C())", "TypeError"),
    ("del *a,", "SyntaxError"),
    ("with 1:\n    pass", "TypeError"),
    ("compile('a +', 'source.py', 'eval')", "SyntaxError"),
    ("compile('a = 1', 'source.py', 'eval')", "SyntaxError"),
    ("eval('1\\x002')", "SyntaxError"),
    ("','.join(['a', 1])", "TypeError"),
    ("'{} {0}'.format(1)", "ValueError"),
    ("'%d' % ()", "TypeError"),
]


def run(command, source, cwd=None):
    return subprocess.run(
        [*command, "-c", source], capture_output=True, text=True, timeout=10, cwd=cwd
    )


def check(source, error=None):
    source = textwrap.dedent(source).strip() + "\n"
    expected = run([sys.executable, "-I"], source)
    actual = run([ENGINE], source)
    if error:
        ok = expected.returncode != 0 and actual.returncode == 1 and error + ":" in actual.stderr
    else:
        ok = expected.returncode == actual.returncode == 0 and actual.stdout == expected.stdout
    if not ok:
        raise AssertionError(
            f"Source:\n{source}\nCPython ({expected.returncode}):\n{expected.stdout}{expected.stderr}"
            f"\nspy ({actual.returncode}):\n{actual.stdout}{actual.stderr}"
        )


def main():
    for source in CASES:
        check(source)
    for source, error in ERRORS:
        check(source, error)
    rng = random.Random(315)
    expressions = []
    for _ in range(300):
        a, b = rng.randint(-100000, 100000), rng.choice([x for x in range(-31, 32) if x])
        op = rng.choice(["+", "-", "*", "//", "%", "&", "|", "^", "<", "<=", ">", ">=", "==", "!="])
        expressions.append(f"print(({a}) {op} ({b}))")
    check("\n".join(expressions))
    floats = []
    while len(floats) < 300:
        value = struct.unpack("d", rng.getrandbits(64).to_bytes(8, sys.byteorder))[0]
        if math.isfinite(value):
            floats.append(f"print({value!r})")
    check("\n".join(floats))
    complex_rng = random.Random(315)
    complex_expressions = []
    for _ in range(300):
        a, b, c, d = [complex_rng.randint(-100, 100) for _ in range(4)]
        op = complex_rng.choice(["+", "-", "*", "/"])
        if c == d == 0:
            c = 1
        complex_expressions.append(f"print(({a}+{b}j){op}({c}+{d}j))")
    # Python 3.15 preserves imaginary signed zeros when the other operand is real.
    if sys.version_info >= (3, 15):
        check('''
class Items:
    def __iter__(self): print('iter'); yield 3; yield 1
class Reverse:
    def __bool__(self): print('reverse'); return True
def key(x): print('key', x); return x
print(sorted(Items(), key=key, reverse=Reverse()))
for reverse in [None, 1.0, [], [1]]:
    print(sorted([3, 1], reverse=reverse))
try: sorted(Items(), unknown=1)
except TypeError: print('unexpected keyword')
''')
        for real in ("0.0", "-0.0", "1.0", "-1.0"):
            for imag in ("0.0", "-0.0"):
                for op in ("+", "-", "*", "/"):
                    for other in ("1.0", "-1.0"):
                        value = f"complex({real}, {imag})"
                        complex_expressions.append(f"print({value}{op}{other})")
                        if op != "/" or real not in ("0.0", "-0.0"):
                            complex_expressions.append(f"print({other}{op}{value})")
    check("\n".join(complex_expressions))
    with tempfile.TemporaryDirectory() as temp:
        Path(temp, "helper.py").write_text("print('loaded')\nx = 40\ndef add(y):\n    return x + y\n")
        source = "import helper\nimport helper as h\nfrom helper import add as f\nprint(helper.x, h is helper, f(2))"
        expected = run([sys.executable], source, temp)
        actual = run([ENGINE], source, temp)
        assert expected.returncode == actual.returncode == 0
        assert expected.stdout == actual.stdout, (expected, actual)
        root = Path(temp)
        (root / '蟒.py').write_text('µ = 42\n')
        source = 'import 蟒\nfrom 蟒 import µ as value\nprint(蟒.μ, value)\n'
        expected = run([sys.executable], source, temp)
        actual = run([ENGINE], source, temp)
        assert expected.returncode == actual.returncode == 0, (expected, actual)
        assert expected.stdout == actual.stdout, (expected, actual)
        package = root / 'pack'
        package.mkdir()
        (root / 'pack.py').write_text("raise AssertionError('package must take precedence')\n")
        (package / '__init__.py').write_text("print('package initialized')\nvalue = 40\nfrom . import child\n__all__ = ['value', 'child']\n")
        (package / 'child.py').write_text("from . import value\nanswer = value + 2\n_private = 99\n")
        nested = package / 'nested'
        nested.mkdir()
        (nested / '__init__.py').write_text("from ..child import answer\n")
        (nested / 'leaf.py').write_text("from .. import child\nfrom ..child import (answer as number, value,)\n")
        (package / 'broken.py').write_text("print('attempt')\nimport unavailable_dependency\n")
        source = """
import pack.child, pack.nested.leaf as leaf
from pack.child import (answer, value as old,)
from pack import *
print(answer, old, value, child is pack.child, leaf.child is child, leaf.number)
print(pack.__name__, pack.__package__, pack.child.__package__, leaf.__package__)
print(__import__('pack.child') is pack)
print(__import__('pack.child', fromlist=['answer']) is child)
print(__import__('child', globals={'__package__': 'pack'}, level=1) is child)
print(__import__('', globals={'__package__': 'pack'}, fromlist=['child'], level=1) is pack)
print(__import__('pack', fromlist=['absent']) is pack)
from pack.child import *
print('_private' in globals(), 'answer' in globals())
for i in range(2):
    try: from pack import broken
    except ModuleNotFoundError: print('dependency failed')
try: from pack import absent
except ImportError: print('missing export')
try: import helper.submodule
except ModuleNotFoundError: print('not a package')
"""
        expected = run([sys.executable], source, temp)
        actual = run([ENGINE], source, temp)
        assert expected.returncode == actual.returncode == 0, (expected, actual)
        assert expected.stdout == actual.stdout, (expected, actual)
    print(f"Differential: {len(CASES)} programs, {len(ERRORS)} errors, 300 integer expressions, 300 floats, {len(complex_expressions)} complex expressions, imports passed")


if __name__ == "__main__":
    main()
