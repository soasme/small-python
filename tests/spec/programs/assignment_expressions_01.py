# spec: PLS-315 13.12
# description: Programs on assignment expressions, each with the output CPython 3.15 gives.
from harness import *

check_program('''def f():
    g = ((saved := i*i) for i in range(3))
    print(next(g), saved, list(g), saved)
    return [(last := x) for x in range(3)], last
print(f())
''',
              '''0 0 [1, 4] 4
([0, 1, 2], 2)
''')

check_program('''[x := 1 for x in range(3)]
''',
              '''SyntaxError: assignment expression cannot rebind comprehension iteration variable 'x' (<program>, line 1)
''')

check_program('''[x for x in (y := range(3))]
''',
              '''SyntaxError: assignment expression cannot be used in a comprehension iterable expression (<program>, line 1)
''')

check_program('''class C:
    x = [(y := 1) for z in range(3)]
''',
              '''SyntaxError: assignment expression within a comprehension cannot be used in a class body (<program>, line 2)
''')
