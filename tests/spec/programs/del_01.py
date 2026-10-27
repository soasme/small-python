# spec: PLS-315 14.7
# description: Programs on del, each with the output CPython 3.15 gives.
from harness import *

check_program('''del __debug__
''',
              '''SyntaxError: cannot delete __debug__ (<program>, line 1)
''')

check_program('''del *a,
''',
              '''SyntaxError: cannot delete starred (<program>, line 1)
''')
