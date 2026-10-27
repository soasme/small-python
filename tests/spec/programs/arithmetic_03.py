# spec: PLS-315 13.7
# description: Programs on arithmetic, each with the output CPython 3.15 gives.
from harness import *

check_program(''''unterminated
''',
              '''SyntaxError: unterminated string literal (detected at line 1) (<program>, line 1)
''')

check_program('''1 = 2
''',
              '''SyntaxError: cannot assign to literal here. Maybe you meant '==' instead of '='? (<program>, line 1)
''')

check_program('''1e+
''',
              '''SyntaxError: invalid decimal literal (<program>, line 1)
''')

check_program('''1__0
''',
              '''SyntaxError: invalid decimal literal (<program>, line 1)
''')

check_program('''0123
''',
              '''SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers (<program>, line 1)
''')

check_program('''1_e2
''',
              '''SyntaxError: invalid decimal literal (<program>, line 1)
''')

check_program('''1e_2
''',
              '''SyntaxError: invalid decimal literal (<program>, line 1)
''')

check_program('''1 + not 2
''',
              '''SyntaxError: 'not' after an operator must be parenthesized (<program>, line 1)
''')

check_program('''(*x), y = 1, 2
''',
              '''SyntaxError: cannot use starred expression here (<program>, line 1)
''')

check_program('''compile('a +', 'source.py', 'eval')
''',
              '''SyntaxError: invalid syntax (source.py, line 1)
''')

check_program('''compile('a = 1', 'source.py', 'eval')
''',
              '''SyntaxError: invalid syntax (source.py, line 1)
''')

check_program("eval('1\\x002')\n",
              '''SyntaxError: source code string cannot contain null bytes
''')
