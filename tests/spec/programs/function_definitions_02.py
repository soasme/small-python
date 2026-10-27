# spec: PLS-315 16.1
# description: Programs on function definitions, each with the output CPython 3.15 gives.
from harness import *

check_program('''def f(**kw): pass
f(**{1: 2})
''',
              '''TypeError: keywords must be strings
''')

check_program('''def f(**kw): pass
f(a=1, **{'a': 2})
''',
              '''TypeError: __main__.f() got multiple values for keyword argument 'a'
''')
