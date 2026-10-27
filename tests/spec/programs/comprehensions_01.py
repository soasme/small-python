# spec: PLS-315 8.6
# description: Programs on comprehensions, each with the output CPython 3.15 gives.
from harness import *

check_program('''x = 50; print([(x, y) for x in range(4) if x for y in range(x) if y]); print(x)
''',
              '''[(2, 1), (3, 1), (3, 2)]
50
''')

check_program('''print({k: v for k, v in zip('ab', [1, 2])}); print(sorted({i % 3 for i in range(10)}))
''',
              '''{'a': 1, 'b': 2}
[0, 1, 2]
''')

check_program('''print(__debug__, [__debug__ for x in range(2)])
''',
              '''True [True, True]
''')

check_program('''[x async for x in a]
''',
              '''SyntaxError: asynchronous comprehension outside of an asynchronous function (<program>, line 1)
''')
