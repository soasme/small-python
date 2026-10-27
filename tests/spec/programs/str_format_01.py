# spec: PLS-315 23.4
# description: Programs on str.format, each with the output CPython 3.15 gives.
from harness import *

check_program('''print('{{{name}}} {0} {name}'.format(5, name='value'))
''',
              '''{value} 5 value
''')

check_program('''format(1, '.2d')
''',
              '''ValueError: Precision not allowed in integer format specifier
''')

check_program('''format('x', '+3')
''',
              '''ValueError: Sign not allowed in string format specifier
''')

check_program(''''{missing}'.format(present=1)
''',
              '''KeyError: 'missing'
''')

check_program(''''{} {0}'.format(1)
''',
              '''ValueError: cannot switch from automatic field numbering to manual field specification
''')
