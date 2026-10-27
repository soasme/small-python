# spec: PLS-315 19.3, 22.3
# description: Programs on round() and float formatting, each with the output CPython 3.15 gives.
from harness import *

check_program('''try:
    value = round(0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(0, -10000)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-1, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-1, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(True, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(True, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(False, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(False, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(0.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(0.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(0.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-0.0, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-0.0, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(2.675, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(2.675, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(0.125, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(0.125, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-0.125)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-0.125, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''int 0
int 0
int 0
int -1
int -1
int 1
int 0
int 0
int 0
int 0
float 0.0
float 0.0
float -0.0
float -0.0
float 3.0
float 0.0
int 0
float 0.125
int 0
float -0.0
''')

check_program('''try:
    value = round(-0.125, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(5e15-1, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(5e15-1, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(5e15, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(5e15, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(5e15+1, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(5e15+1, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(5e15+2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(5e15+2, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(5e15+2, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(5e15+3, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(5e15+3, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1.7976931348623157e308, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1.7976931348623157e308, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(5e-324, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(5e-324, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(float('inf'))
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(float('inf'), -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(float('inf'), -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(float('-inf'), 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float -0.0
float 4999999999999999.0
float 4999999999999999.0
float 5000000000000000.0
float 0.0
int 5000000000000001
float 5000000000000001.0
int 5000000000000002
float 5000000000000000.0
float 0.0
float 5000000000000003.0
float 5000000000000003.0
float 1.7976931348623157e+308
OverflowError
int 0
float 0.0
OverflowError
float inf
float inf
float -inf
''')

check_program('''try:
    value = round(float('-inf'), 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(float('nan'), 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(float('nan'), -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-50.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-50.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-50.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-50.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-50.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-49.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-49.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-49.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-49.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-48.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-48.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-48.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-48.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-48.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-47.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-47.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-47.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float -inf
float nan
float nan
int -50
float -50.5
int -50
float -0.0
float -0.0
float -49.5
float -49.5
float -49.0
float -0.0
int -48
float -48.5
int -48
float -0.0
float -0.0
float -47.5
float -47.5
float -47.0
''')

check_program('''try:
    value = round(-47.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-46.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-46.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-46.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-46.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-46.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-45.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-45.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-45.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-45.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-44.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-44.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-44.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-44.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-44.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-43.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-43.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-43.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-43.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-42.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float -0.0
int -46
float -46.5
int -46
float -0.0
float -0.0
float -45.5
float -45.5
float -45.0
float -0.0
int -44
float -44.5
int -44
float -0.0
float -0.0
float -43.5
float -43.5
float -43.0
float -0.0
int -42
''')

check_program('''try:
    value = round(-42.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-42.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-42.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-42.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-41.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-41.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-41.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-41.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-40.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-40.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-40.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-40.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-40.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-39.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-39.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-39.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-39.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-38.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-38.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-38.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float -42.5
int -42
float -0.0
float -0.0
float -41.5
float -41.5
float -41.0
float -0.0
int -40
float -40.5
int -40
float -0.0
float -0.0
float -39.5
float -39.5
float -39.0
float -0.0
int -38
float -38.5
int -38
''')

check_program('''try:
    value = round(-38.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-38.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-37.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-37.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-37.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-37.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-36.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-36.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-36.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-36.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-36.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-35.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-35.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-35.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-35.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-34.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-34.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-34.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-34.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-34.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float -0.0
float -0.0
float -37.5
float -37.5
float -37.0
float -0.0
int -36
float -36.5
int -36
float -0.0
float -0.0
float -35.5
float -35.5
float -35.0
float -0.0
int -34
float -34.5
int -34
float -0.0
float -0.0
''')

check_program('''try:
    value = round(-33.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-33.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-33.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-33.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-32.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-32.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-32.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-32.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-32.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-31.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-31.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-31.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-31.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-30.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-30.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-30.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-30.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-30.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-29.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-29.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float -33.5
float -33.5
float -33.0
float -0.0
int -32
float -32.5
int -32
float -0.0
float -0.0
float -31.5
float -31.5
float -31.0
float -0.0
int -30
float -30.5
int -30
float -0.0
float -0.0
float -29.5
float -29.5
''')

check_program('''try:
    value = round(-29.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-29.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-28.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-28.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-28.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-28.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-28.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-27.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-27.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-27.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-27.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-26.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-26.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-26.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-26.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-26.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-25.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-25.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-25.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-25.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float -29.0
float -0.0
int -28
float -28.5
int -28
float -0.0
float -0.0
float -27.5
float -27.5
float -27.0
float -0.0
int -26
float -26.5
int -26
float -0.0
float -0.0
float -25.5
float -25.5
float -25.0
float -0.0
''')

check_program('''try:
    value = round(-24.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-24.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-24.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-24.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-24.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-23.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-23.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-23.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-23.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-22.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-22.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-22.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-22.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-22.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-21.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-21.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-21.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-21.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-20.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-20.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''int -24
float -24.5
int -24
float -0.0
float -0.0
float -23.5
float -23.5
float -23.0
float -0.0
int -22
float -22.5
int -22
float -0.0
float -0.0
float -21.5
float -21.5
float -21.0
float -0.0
int -20
float -20.5
''')

check_program('''try:
    value = round(-20.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-20.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-20.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-19.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-19.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-19.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-19.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-18.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-18.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-18.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-18.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-18.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-17.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-17.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-17.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-17.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-16.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-16.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-16.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-16.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''int -20
float -0.0
float -0.0
float -19.5
float -19.5
float -19.0
float -0.0
int -18
float -18.5
int -18
float -0.0
float -0.0
float -17.5
float -17.5
float -17.0
float -0.0
int -16
float -16.5
int -16
float -0.0
''')

check_program('''try:
    value = round(-16.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-15.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-15.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-15.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-15.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-14.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-14.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-14.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-14.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-14.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-13.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-13.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-13.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-13.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-12.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-12.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-12.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-12.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-12.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-11.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float -0.0
float -15.5
float -15.5
float -15.0
float -0.0
int -14
float -14.5
int -14
float -0.0
float -0.0
float -13.5
float -13.5
float -13.0
float -0.0
int -12
float -12.5
int -12
float -0.0
float -0.0
float -11.5
''')

check_program('''try:
    value = round(-11.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-11.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-11.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-10.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-10.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-10.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-10.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-10.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-9.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-9.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-9.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-9.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-8.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-8.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-8.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-8.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-8.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-7.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-7.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-7.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float -11.5
float -11.0
float -0.0
int -10
float -10.5
int -10
float -0.0
float -0.0
float -9.5
float -9.5
float -9.0
float -0.0
int -8
float -8.5
int -8
float -0.0
float -0.0
float -7.5
float -7.5
float -7.0
''')

check_program('''try:
    value = round(-7.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-6.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-6.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-6.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-6.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-6.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-5.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-5.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-5.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-5.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-4.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-4.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-4.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-4.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-4.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-3.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-3.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-3.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-3.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-2.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float -0.0
int -6
float -6.5
int -6
float -0.0
float -0.0
float -5.5
float -5.5
float -5.0
float -0.0
int -4
float -4.5
int -4
float -0.0
float -0.0
float -3.5
float -3.5
float -3.0
float -0.0
int -2
''')

check_program('''try:
    value = round(-2.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-2.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-2.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-2.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-1.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-1.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-1.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-1.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-0.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(-0.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(0.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(0.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(0.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(0.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(0.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(1.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(2.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float -2.5
int -2
float -0.0
float -0.0
float -1.5
float -1.5
float -1.0
float -0.0
int 0
float -0.5
int 0
float 0.0
float 0.0
float 0.5
float 0.5
float 1.0
float 0.0
int 2
float 1.5
int 2
''')

check_program('''try:
    value = round(2.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(2.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(2.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(2.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(3.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(3.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(3.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(3.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(4.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(4.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(4.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(4.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(4.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(5.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(5.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(5.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(5.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(6.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(6.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(6.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float 0.0
float 0.0
float 2.5
float 2.5
float 3.0
float 0.0
int 4
float 3.5
int 4
float 0.0
float 0.0
float 4.5
float 4.5
float 5.0
float 0.0
int 6
float 5.5
int 6
float 0.0
float 0.0
''')

check_program('''try:
    value = round(6.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(6.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(7.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(7.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(7.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(7.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(8.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(8.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(8.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(8.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(8.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(9.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(9.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(9.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(9.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(10.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(10.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(10.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(10.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(10.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float 6.5
float 6.5
float 7.0
float 0.0
int 8
float 7.5
int 8
float 0.0
float 0.0
float 8.5
float 8.5
float 9.0
float 0.0
int 10
float 9.5
int 10
float 0.0
float 0.0
float 10.5
float 10.5
''')

check_program('''try:
    value = round(11.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(11.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(11.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(11.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(12.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(12.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(12.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(12.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(12.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(13.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(13.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(13.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(13.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(14.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(14.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(14.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(14.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(14.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(15.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(15.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float 11.0
float 0.0
int 12
float 11.5
int 12
float 0.0
float 0.0
float 12.5
float 12.5
float 13.0
float 0.0
int 14
float 13.5
int 14
float 0.0
float 0.0
float 14.5
float 14.5
float 15.0
float 0.0
''')

check_program('''try:
    value = round(15.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(15.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(16.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(16.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(16.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(16.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(16.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(17.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(17.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(17.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(17.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(18.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(18.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(18.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(18.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(18.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(19.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(19.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(19.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(19.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''int 16
float 15.5
int 16
float 0.0
float 0.0
float 16.5
float 16.5
float 17.0
float 0.0
int 18
float 17.5
int 18
float 0.0
float 0.0
float 18.5
float 18.5
float 19.0
float 0.0
int 20
float 19.5
''')

check_program('''try:
    value = round(20.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(20.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(20.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(20.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(20.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(21.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(21.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(21.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(21.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(22.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(22.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(22.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(22.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(22.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(23.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(23.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(23.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(23.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(24.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(24.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''int 20
float 0.0
float 0.0
float 20.5
float 20.5
float 21.0
float 0.0
int 22
float 21.5
int 22
float 0.0
float 0.0
float 22.5
float 22.5
float 23.0
float 0.0
int 24
float 23.5
int 24
float 0.0
''')

check_program('''try:
    value = round(24.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(24.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(24.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(25.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(25.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(25.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(25.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(26.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(26.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(26.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(26.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(26.5, 10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(27.0, 0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(27.0, -308)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(27.5, None)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(27.5, 323)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(28.0)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(28.0, -2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(28.0, -10**100)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
try:
    value = round(28.5, 2)
    print(type(value).__name__, repr(value))
except Exception as error: print(type(error).__name__)
''',
              '''float 0.0
float 24.5
float 24.5
float 25.0
float 0.0
int 26
float 25.5
int 26
float 0.0
float 0.0
float 26.5
float 26.5
float 27.0
float 0.0
int 28
float 27.5
int 28
float 0.0
float 0.0
float 28.5
''')
