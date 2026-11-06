# spec: PLS-315 19.3.27, 27.2.1, 27.2, 27.3
# description: next() and a generator's __next__ and send resume it to
# its next yield, whose value it returns; send's value is what that yield
# evaluates to. A generator that returns raises StopIteration with its
# value, unless next() has a default; what it raises reaches the caller.
# A coroutine's send runs it the same way.
from harness import *

def echo():
    x = yield 1
    y = yield x * 2
    return ('done', y)

def resumed():
    g = echo()
    out = [next(g), g.send(5)]
    try:
        g.send(7)
    except StopIteration as e:
        out.append(e.value)
    h = echo()
    out.append(h.__next__())
    send = h.send
    out.append(send(3))
    out.append(next(echo(), 'unused'))
    return out

assert resumed() == [1, 10, ('done', 7), 1, 6, 1], resumed()

# At module level, too.
g = echo()
assert next(g) == 1 and g.send(4) == 8

def short():
    yield 0

def defaults():
    g = short()
    next(g)
    return next(g, 'default'), next(g, None)

assert defaults() == ('default', None)

def returning():
    return 4
    yield

def stopped():
    out = []
    try:
        next(returning())
    except StopIteration as e:
        out.append(e.args)
    g = short()
    next(g)
    try:
        g.__next__()
    except StopIteration as e:
        out.append(e.args)
    try:
        echo().send(1)
    except TypeError as e:
        out.append(str(e))
    return out

assert stopped() == [(4,), (), "can't send non-None value to a just-started generator"], stopped()

def failing():
    yield 1
    raise KeyError(2)

def raised():
    g = failing()
    next(g)
    out = []
    try:
        next(g, 'default')
    except KeyError as e:
        out.append(e.args)
    try:
        next(g)
    except StopIteration as e:
        out.append(('stop', e.args))
    return out

assert raised() == [(2,), ('stop', ())], raised()

# A generator resuming itself is already running.
def itself():
    yield next(me)

me = itself()
try:
    next(me)
except ValueError as e:
    assert str(e) == 'generator already executing'
else:
    raise AssertionError('no ValueError')

# Coroutines.
async def f(x):
    n = 0
    for i in range(3): n += i
    return n + x
def coroutines():
    out = []
    c = f(1)
    try: c.send(None)
    except StopIteration as e: out.append(e.value)
    try: c.send(None)
    except RuntimeError as e: out.append(str(e))
    c = f(2)
    try: c.send(3)
    except TypeError as e: out.append(str(e))
    c.close()
    async def stop():
        raise StopIteration(5)
    try: stop().send(None)
    except RuntimeError as e: out.append(str(e))
    async def bad():
        raise KeyError(1)
    try: bad().send(None)
    except KeyError as e: out.append(e.args)
    class Y:
        def __await__(self):
            v = yield 'y'
            return v
    async def waits():
        return await Y()
    w = waits()
    out.append(w.send(None))
    try: w.send(9)
    except StopIteration as e: out.append(e.value)
    s = f(4).send
    try: s(None)
    except StopIteration as e: out.append(e.value)
    return out
assert coroutines() == [4, 'cannot reuse already awaited coroutine', "can't send non-None value to a just-started coroutine",
                 'coroutine raised StopIteration', (1,), 'y', 9, 7], coroutines()
c = f(5)
try:
    c.send(None)
except StopIteration as e:
    assert e.value == 8
else:
    raise AssertionError('no StopIteration')
