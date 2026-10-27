# spec: PLS-315 16.4
# description: Programs on class definitions, each with the output CPython 3.15 gives.
from harness import *

check_program('''class C:
    def __bool__(self): return 1
bool(C())
''',
              '''TypeError: C.__bool__() must return a bool, not int
''')

check_program('''class C:
    def __str__(self): return 1
str(C())
''',
              '''TypeError: C.__str__() must return a str, not int
''')
