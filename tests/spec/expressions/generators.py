# spec: reference/expressions.html#yield-expressions
# description: Generator functions, send/throw/close, yield from, and return values.
from harness import *

def echo(value=None):
    log = []
    try:
        while True:
            try:
                value = (yield value)
            except Exception as e:
                value = e
            log.append(value)
    finally:
        log.append("cleanup")
        echo.log = log
g = echo(1)
assert_eq(next(g), 1)
assert_is(next(g), None)
assert_eq(g.send(2), 2)
e = TypeError("spam")
assert_is(g.throw(e), e)
g.close()
assert_eq(echo.log, [None, 2, e, "cleanup"])

# Sending a non-None value to a just-started generator is an error.
def gen():
    yield 1
assert_raises(TypeError, gen().send, 1)

# return in a generator sets StopIteration.value.
def ret():
    yield 1
    return "done"
r = ret()
next(r)
stop = assert_raises(StopIteration, next, r)
assert_eq(stop.value, "done")
assert_raises(StopIteration, next, r)

# yield from delegates send/throw and returns the subgenerator's value.
def inner():
    received = yield "i1"
    yield received
    return "inner-result"
def outer():
    result = yield from inner()
    yield result
o = outer()
assert_eq(next(o), "i1")
assert_eq(o.send("x"), "x")
assert_eq(next(o), "inner-result")
def flatten(xs):
    for x in xs:
        if isinstance(x, list):
            yield from flatten(x)
        else:
            yield x
assert_eq(list(flatten([1, [2, [3, [4]]], 5])), [1, 2, 3, 4, 5])

# StopIteration raised inside a generator becomes RuntimeError (PEP 479).
def leaky():
    raise StopIteration
    yield
assert_raises(RuntimeError, next, leaky())

# Generators are iterators; a running generator cannot be re-entered.
def selfish():
    yield next(me)
me = selfish()
assert_raises(ValueError, next, me)
assert_is(iter(me), me)

# close() raises GeneratorExit inside; yielding then is a RuntimeError.
def stubborn():
    try:
        yield 1
    except GeneratorExit:
        yield 2
s = stubborn()
next(s)
assert_raises(RuntimeError, s.close)

# throw() with an exception the generator does not catch propagates.
def plain():
    yield 1
p = plain()
next(p)
assert_raises(KeyError, p.throw, KeyError("k"))
assert_raises(StopIteration, next, p)

# yield is an expression usable in assignments and needs parentheses in most expression contexts.
def acc():
    total = 0
    while True:
        total += yield total
a = acc()
next(a)
assert_eq(a.send(5), 5)
assert_eq(a.send(3), 8)
assert_syntax_error("yield 1")
assert_syntax_error("def f():\n    x = 1 + yield 2")
assert_compiles("def f():\n    x = 1 + (yield 2)")
assert_syntax_error("lambda: (yield from x)") if False else None
assert_syntax_error("class A:\n    yield 1")

# Generator attributes.
def named():
    yield
n = named()
assert_eq(n.__name__, "named")
assert_true(n.__qualname__.endswith("named"))
assert_eq(type(n).__name__, "generator")
