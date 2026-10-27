# spec: PLS-315 14.14
# description: Programs on global and nonlocal, each with the output CPython 3.15 gives.
from harness import *

check_program('''x = 10
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
''',
              '''1 2 1 0 10
12 1 12
''')

check_program('''x = 0
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
''',
              '''[0, 1, 2]
2
[0, 1, 2] 2
42
''')

check_program('''def outer():
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
''',
              '''{'a': 1, 'b': 2, 'free': 11} 1 3 12
''')

check_program('''nonlocal x
''',
              '''SyntaxError: nonlocal declaration not allowed at module level (<program>, line 1)
''')

check_program('''def f():
 nonlocal missing
''',
              '''SyntaxError: no binding for nonlocal 'missing' found (<program>, line 2)
''')

check_program('''def f(x):
 global x
''',
              '''SyntaxError: name 'x' is parameter and global (<program>, line 2)
''')

check_program('''def f(x):
 nonlocal x
''',
              '''SyntaxError: name 'x' is parameter and nonlocal (<program>, line 2)
''')

check_program('''def f():
 x=1
 global x
''',
              '''SyntaxError: name 'x' is assigned to before global declaration (<program>, line 3)
''')

check_program('''def f():
 print(x)
 global x
''',
              '''SyntaxError: name 'x' is used prior to global declaration (<program>, line 3)
''')

check_program('''def f():
 x=1
 nonlocal x
''',
              '''SyntaxError: name 'x' is assigned to before nonlocal declaration (<program>, line 3)
''')

check_program('''def f():
 global x
 nonlocal x
''',
              '''SyntaxError: name 'x' is nonlocal and global (<program>, line 2)
''')

check_program('''def f():
 global x
 def g():
  nonlocal x
''',
              '''SyntaxError: no binding for nonlocal 'x' found (<program>, line 4)
''')

check_program('''class C:
 x=1
 def f(self):
  nonlocal x
''',
              '''SyntaxError: no binding for nonlocal 'x' found (<program>, line 4)
''')

check_program('''def f():
 global x
 x=1
 global x
''',
              '''SyntaxError: name 'x' is assigned to before global declaration (<program>, line 4)
''')
