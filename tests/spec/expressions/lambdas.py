# spec: PLS-315 13.14, 16.1, 16.2
# description: A lambda makes a function named <lambda> whose body returns its expression.
from harness import *

f = lambda: 1
assert_eq(f(), 1)
assert_eq(f.__name__, "<lambda>")
assert_eq(f.__qualname__, "<lambda>")
assert_type(f, type(lambda: None))
g = lambda a, b=2, *args, c, d=4, **kw: (a, b, args, c, d, kw)
assert_eq(g(1, c=3), (1, 2, (), 3, 4, {}))
assert_eq(g(1, 5, 6, c=3, e=7), (1, 5, (6,), 3, 4, {"e": 7}))
h = lambda x, /, y: (x, y)
assert_eq(h(1, y=2), (1, 2))
assert_raises(TypeError, lambda: h(x=1, y=2))
assert_eq(g.__defaults__, (2,))
assert_eq(g.__kwdefaults__, {"d": 4})
assert_eq(f.__annotations__, {})

# Defaults are evaluated once, when the lambda is evaluated.
count = []
k = lambda x=count.append(1): x
k(); k()
assert_eq(count, [1])

# Closures capture variables, not values.
fs = [lambda: i for i in range(3)]
assert_eq([fn() for fn in fs], [2, 2, 2])
fs = [lambda i=i: i for i in range(3)]
assert_eq([fn() for fn in fs], [0, 1, 2])

# Nested qualname.
def outer():
    return lambda: None
assert_eq(outer().__qualname__, "outer.<locals>.<lambda>")

# The body is an expression: no statements, no annotations.
assert_syntax_error("lambda: return 1\n")
assert_syntax_error("lambda x: int: x\n")
assert_syntax_error("lambda (x): x\n")
# A lambda body may yield, making a generator function.
gen = lambda: (yield 1)
assert_eq(list(gen()), [1])
