# spec: PLS-315 25.1
# description: Programs on lists, each with the output CPython 3.15 gives.
from harness import *

check_program('''[1,2][::0]
''',
              '''ValueError: slice step cannot be zero
''')

check_program('''[1][2]
''',
              '''IndexError: list index out of range
''')

check_program('''{}['x']
''',
              '''KeyError: 'x'
''')

check_program('''{}[[]]
''',
              '''TypeError: cannot use 'list' as a dict key (unhashable type: 'list')
''')

check_program('''[].pop()
''',
              '''IndexError: pop from empty list
''')

check_program('''[] in {}
''',
              '''TypeError: cannot use 'list' as a dict key (unhashable type: 'list')
''')
