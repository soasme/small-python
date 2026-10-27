# spec: PLS-315 13.7
# description: Programs on arithmetic, each with the output CPython 3.15 gives.
from harness import *

check_program('''print('Hello, world!')
''',
              '''Hello, world!
''')

check_program('''print(1 + 2 * 3, (1 + 2) * 3, -2**2, (-2)**2, 2**-2, 2**3**2)
''',
              '''7 9 -4 4 0.25 512
''')

check_program('''print(-7 // 3, -7 % 3, 7 // -3, 7 % -3, -7 // -3, -7 % -3)
''',
              '''-3 2 -3 -2 2 -1
''')

check_program('''print(1 if True else missing, missing if False else 2)
''',
              '''1 2
''')

check_program("print('a\\nb', 'c\\td', 'quote: \\'', '\\\\', '\\x41')\n",
              "a\nb c\td quote: ' \\ A\n")

check_program("print('''hello\nworld''')\n",
              '''hello
world
''')

check_program('''x = 5; x += 2; x *= 3; x -= 1; x %= 6; x /= 2; print(x)
''',
              '''1.0
''')

check_program('''x = (
    1 +
    2
)
print(x)
''',
              '''3
''')

check_program('x = 1 + \\\n    2\nprint(x)\n',
              '''3
''')

check_program('''# comment

if True:
    # comment
    print(42)

# last
''',
              '''42
''')

check_program('''if True: print(1); print(2)
print(3)
''',
              '''1
2
3
''')

check_program('''print(__name__)
''',
              '''__main__
''')

check_program('''if True:
    x = (
        1 + 2
    )
    print(x)
print(4)
''',
              '''3
4
''')

check_program('''code = compile('a + 2', 'generated.py', 'eval'); a = 40; print(eval(code), eval('a + 3'))
''',
              '''42 43
''')

check_program('''exec('value = 42'); print(value, exec('1 + 2'))
''',
              '''42 None
''')

check_program('''print(..., ... is Ellipsis, type(...)() is ..., type(None)() is None, type(NotImplemented)() is NotImplemented)
''',
              '''Ellipsis True True True True
''')

check_program('''__import__('')
''',
              '''ValueError: Empty module name
''')

check_program('''__import__(42)
''',
              '''TypeError: module name must be a string
''')

check_program('''__import__('x', level=-1)
''',
              '''ValueError: level must be >= 0
''')

check_program('''bool(NotImplemented)
''',
              '''TypeError: NotImplemented should not be used in a boolean context
''')
