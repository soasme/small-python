# spec: PLS-315 10.3, 7.3.2, 7.5.1
# description: A class without __bool__ whose __len__ is a descriptor
# takes its truth from the read's result called, checked as a length:
# zero is false, a negative length raises ValueError and a non-integer
# TypeError; an error of the read, AttributeError too, propagates.
# bool(), bool by a star call, filter(), a comprehension's if, any(),
# all(), not and a conditional agree, each reading it once.
from harness import *

log = []
def booh(self): raise AttributeError("booh")
def boom(self): raise KeyError("boom")
def length(n):
    def get(self):
        for _ in (): pass
        log.append(("get", n))
        return lambda: n
    return property(get)
classes = [type("L%d" % i, (), {"__len__": p}) for i, p in enumerate([length(0), length(2), property(booh), property(boom), length(-1), length("x")])]
def attempt(f):
    try: return f()
    except Exception as e: return type(e).__name__
def call(f, *a): return f(*a)
def machine(x):
    for _ in (): pass
    out = [attempt(lambda: bool(x)), attempt(lambda: call(bool, x)), attempt(lambda: list(filter(None, [x])) == [x]),
           attempt(lambda: [1 for y in [x] if y]), attempt(lambda: any([x])), attempt(lambda: all([x]))]
    try: out.append(not x)
    except Exception as e: out.append(type(e).__name__)
    try: out.append(1 if x else 0)
    except Exception as e: out.append(type(e).__name__)
    return out
def results():
    del log[:]
    return [machine(k()) for k in classes], list(log)

expected = ([[False, False, False, [], False, False, True, 0], [True, True, True, [1], True, True, False, 1], ['AttributeError', 'AttributeError', 'AttributeError', 'AttributeError', 'AttributeError', 'AttributeError', 'AttributeError', 'AttributeError'], ['KeyError', 'KeyError', 'KeyError', 'KeyError', 'KeyError', 'KeyError', 'KeyError', 'KeyError'], ['ValueError', 'ValueError', 'ValueError', 'ValueError', 'ValueError', 'ValueError', 'ValueError', 'ValueError'], ['TypeError', 'TypeError', 'TypeError', 'TypeError', 'TypeError', 'TypeError', 'TypeError', 'TypeError']], [('get', 0), ('get', 0), ('get', 0), ('get', 0), ('get', 0), ('get', 0), ('get', 0), ('get', 0), ('get', 2), ('get', 2), ('get', 2), ('get', 2), ('get', 2), ('get', 2), ('get', 2), ('get', 2), ('get', -1), ('get', -1), ('get', -1), ('get', -1), ('get', -1), ('get', -1), ('get', -1), ('get', -1), ('get', 'x'), ('get', 'x'), ('get', 'x'), ('get', 'x'), ('get', 'x'), ('get', 'x'), ('get', 'x'), ('get', 'x')])

assert_eq(results(), expected)
assert_eq(results(), expected)
