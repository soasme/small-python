# spec: PLS-315 13.7
# description: Programs on arithmetic, each with the output CPython 3.15 gives.
from harness import *

check_program('''1 @ 2
''',
              '''TypeError: unsupported operand type(s) for @: 'int' and 'int'
''')

check_program('''__debug__ = 1
''',
              '''SyntaxError: cannot assign to __debug__ (<program>, line 1)
''')

check_program('''obj.__debug__ = 1
''',
              '''SyntaxError: cannot assign to __debug__ (<program>, line 1)
''')

check_program('''f(__debug__=1)
''',
              '''SyntaxError: cannot assign to __debug__ (<program>, line 1)
''')

check_program('''print(1, sep=1)
''',
              '''AttributeError: 'int' object has no attribute 'join'
''')

check_program('''print(1, end=1)
''',
              '''TypeError: can only concatenate str (not "int") to str
''')

check_program('''print(1, nope=1)
''',
              '''TypeError: run_program.<locals>.print_() got an unexpected keyword argument 'nope'
''')

check_program('''1 / 0
''',
              '''ZeroDivisionError: division by zero
''')

check_program('''1 // 0
''',
              '''ZeroDivisionError: division by zero
''')

check_program('''1 % 0
''',
              '''ZeroDivisionError: division by zero
''')

check_program('''0 ** -1
''',
              '''ZeroDivisionError: zero to a negative power
''')

check_program('''missing
''',
              '''NameError: name 'missing' is not defined
''')

check_program('''1 + 'x'
''',
              '''TypeError: unsupported operand type(s) for +: 'int' and 'str'
''')

check_program('''1(2)
''',
              '''TypeError: 'int' object is not callable
''')

check_program('''len(1)
''',
              '''TypeError: object of type 'int' has no len()
''')

check_program('''return 1
''',
              '''SyntaxError: 'return' outside function (<program>, line 1)
''')

check_program('''break
''',
              '''SyntaxError: 'break' outside loop (<program>, line 1)
''')

check_program('''continue
''',
              '''SyntaxError: 'continue' not properly in loop (<program>, line 1)
''')

check_program('''if:
 pass
''',
              '''SyntaxError: invalid syntax (<program>, line 1)
''')

check_program('''(1]
''',
              '''SyntaxError: closing parenthesis ']' does not match opening parenthesis '(' (<program>, line 1)
''')
