# spec: PLS-315 26.1
# description: Programs on dicts, each with the output CPython 3.15 gives.
from harness import *

check_program('''d = {1: 'first', True: 'second'}; print(d, len(d), 1 in d)
''',
              '''{1: 'second'} 1 True
''')

check_program('''print(tuple(range(3)), list('abc'), list((1, 2)), list({'x': 3}))
''',
              '''(0, 1, 2) ['a', 'b', 'c'] [1, 2] ['x']
''')

check_program('''print(int(), float(), bool(), str(), list(), tuple(), dict())
''',
              '''0 0.0 False  [] () {}
''')

check_program('''{[]: 1}
''',
              '''TypeError: cannot use 'list' as a dict key (unhashable type: 'list')
''')
