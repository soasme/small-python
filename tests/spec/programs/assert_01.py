# spec: PLS-315 14.5
# description: Programs on assert, each with the output CPython 3.15 gives.
from harness import *

check_program('''assert False, 'oops'
''',
              '''AssertionError: oops
''')
