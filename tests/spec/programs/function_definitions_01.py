# spec: PLS-315 16.1
# description: Programs on function definitions, each with the output CPython 3.15 gives.
from harness import *

check_program('''def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)
print(fib(12))
''',
              '''144
''')

check_program('''def make(x):
    def add(y):
        return x + y
    return add
a = make(2)
b = make(3)
print(a(4), b(4), a(7))
''',
              '''6 7 9
''')

check_program('''def f(n):
    for x in range(n):
        if x == 3:
            return x
    return -1
print(f(5), f(2))
''',
              '''3 -1
''')

check_program('''def nothing(): pass
print(nothing())
''',
              '''None
''')

check_program('''calls = []
def middle():
    calls.append(1)
    return 2
print(1 < middle() < 3, calls)
print(4 < middle() < missing, calls)
''',
              '''True [1]
False [1, 1]
''')

check_program('''calls = []
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
''',
              '''[5] ['index', 'rhs']
[3] ['rhs', 'index']
''')

check_program('''code = compile('def f(x): return x + 2', 'generated.py', 'exec'); exec(code); print(f(40), eval(code))
''',
              '''42 None
''')

check_program('''log = []
def mark(x):
    log.append(x)
    return x
def f(a, b):
    return a, b
print(f(b=mark(2), *[mark(1)]), log)
''',
              '''(1, 2) [1, 2]
''')

check_program('''def make(n):
    return ((i, j) for i in range(n) for j in range(i) if j % 2 == 0)
g = make(4)
print(next(g), list(g), list(g))
x = 3
g = (i * x for i in range(x))
x = 4
print(list(g))
''',
              '''(1, 0) [(2, 0), (3, 0), (3, 2)] []
[0, 4, 8]
''')

check_program('''x = 3
g = globals()
g['x'] = 4
print(x, g is globals(), locals() is globals())
def f():
    return globals() is g
print(f(), f.__globals__ is g)
''',
              '''4 True True
True True
''')

check_program('''def f():
    'documentation'
f.extra = f
f.__dict__.update(a=1)
f.__name__ = 'renamed'
print(f.__name__, f.__qualname__, f.__doc__, f.extra is f, f.a)
wrapper = staticmethod(f)
print(wrapper.__name__ is f.__name__, wrapper.__annotations__ is f.__annotations__)
f.__name__ = 'later'
print(wrapper.__name__, f.__name__)
''',
              '''renamed f documentation True 1
True True
renamed later
''')

check_program('''def f():
    return [x async for x in a]
''',
              '''SyntaxError: asynchronous comprehension outside of an asynchronous function (<program>, line 2)
''')

check_program('''def f(__debug__): pass
''',
              '''SyntaxError: cannot assign to __debug__ (<program>, line 1)
''')

check_program('''def f(a): return a
f()
''',
              '''TypeError: f() missing 1 required positional argument: 'a'
''')

check_program('''x = 1
def f():
    print(x)
    x = 2
f()
''',
              '''UnboundLocalError: cannot access local variable 'x' where it is not associated with a value
''')

check_program('''def f():
    if False:
        x = 1
    return x
f()
''',
              '''UnboundLocalError: cannot access local variable 'x' where it is not associated with a value
''')

check_program('''def f(a, a): pass
''',
              '''SyntaxError: duplicate parameter 'a' in function definition (<program>, line 1)
''')

check_program('''def f(a): pass
f(1, a=2)
''',
              '''TypeError: f() got multiple values for argument 'a'
''')

check_program('''def f(*, a): pass
f(1)
''',
              '''TypeError: f() takes 0 positional arguments but 1 was given
''')

check_program('''def f(a, /): pass
f(a=1)
''',
              '''TypeError: f() got some positional-only arguments passed as keyword arguments: 'a'
''')
