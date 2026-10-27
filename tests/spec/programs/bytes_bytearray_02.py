# spec: PLS-315 24.3
# description: Programs on bytes and bytearray, each with the output CPython 3.15 gives.
from harness import *

check_program(''''a' + b'b'
''',
              '''TypeError: can only concatenate str (not "bytes") to str
''')

check_program('''b'a'[0] = 2
''',
              '''TypeError: 'bytes' object does not support item assignment
''')

check_program('''256 in b'abc'
''',
              '''ValueError: byte must be in range(0, 256)
''')

check_program(''''a' in b'abc'
''',
              '''TypeError: a bytes-like object is required, not 'str'
''')
