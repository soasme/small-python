# spec: PLS-315 13.9
# description: Programs on bitwise operators, each with the output CPython 3.15 gives.
from harness import *

check_program('''print(1 << 5, -9 >> 2, 15 & 6, 15 | 16, 9 ^ 3, ~7)
''',
              '''32 -3 6 31 10 -8
''')

check_program('''print(True & False, True | False, True ^ True, True & 3)
''',
              '''False True False 1
''')

check_program('''1 << -1
''',
              '''ValueError: negative shift count
''')
