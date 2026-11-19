# spec: PLS-315 9.2.3, 8.4
# description: a function made in a call keeps only the variables its
# scope, or a scope nested in it, reads from that call (its cells); the
# call's other locals are released when it returns, as weak references
# show. A class body or a comprehension reading a local keeps it too; a
# frame object of the call, through a traceback, keeps every local; a
# nested definition's annotations read cells too.
from harness import *

class Big: pass

def lambda_only():
    big = Big()
    return (lambda: 1), host.weak_reference(big)
f, r = lambda_only()
assert_is(r(), None)
assert_eq(f(), 1)

def reads_other():
    big, kept = Big(), Big()
    def g(): return kept
    return g, host.weak_reference(big), host.weak_reference(kept)
g, r, k = reads_other()
assert_is(r(), None)
assert_is(k(), g())

def nested_reader():
    big, deep = Big(), Big()
    def outer():
        def inner(): return deep
        return inner
    return outer, host.weak_reference(big), host.weak_reference(deep)
o, r, k = nested_reader()
assert_is(r(), None)
assert_is(k(), o()())

def class_reader():
    big, value = Big(), Big()
    class C:
        attr = value
        def m(self): return 0
    return C, host.weak_reference(big), host.weak_reference(value)
C, r, k = class_reader()
assert_is(r(), None)
assert_is(k(), C.attr)

def comprehension_reader():
    big, item = Big(), Big()
    gen = (item for _ in range(1))
    return gen, host.weak_reference(big), host.weak_reference(item)
gen, r, k = comprehension_reader()
assert_is(r(), None)
assert_is(next(gen), k())

# A non-cell name is not visible to a closure's eval() once the call returned.
def evaluator():
    hidden = 1
    shown = 2
    return lambda: (shown, eval("hidden"))
e = assert_raises(NameError, evaluator())
assert_eq(str(e), "name 'hidden' is not defined")

# A traceback's frame keeps all of the call's locals.
def raiser():
    big = Big()
    def g(): return 1
    ref = host.weak_reference(big)
    raise ValueError(g, ref)
try: raiser()
except ValueError as exc:
    tb = exc.__traceback__
    g, ref = exc.args
assert_true(ref() is not None)
assert_is(tb.tb_next.tb_frame.f_locals["big"], ref())

# A nested definition's annotations are a nested scope: what they read is a
# cell (co_cellvars), there when they are evaluated after the call returned.
def annotated():
    q, big = float, Big()
    def inner(x: q) -> q: pass
    return inner, host.weak_reference(big)
inner, r = annotated()
assert_eq(annotated.__code__.co_cellvars, ("q",))
assert_is(r(), None)
assert_eq(inner.__annotations__, {"x": float, "return": float})
