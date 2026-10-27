# spec: PLS-315 15.4
# description: Programs on try statements, each with the output CPython 3.15 gives.
from harness import *

check_program('''try:
    1 / 0
except 42:
    pass
''',
              '''TypeError: catching classes that do not inherit from BaseException is not allowed
''')
