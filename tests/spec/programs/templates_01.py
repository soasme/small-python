# spec: PLS-315 12.5, 23.7
# description: Programs on template strings and their malformed forms, each with the output CPython 3.15 gives.
from harness import *

check_program('\nfor source, message in (("t\'", \'unterminated t-string literal\'), ("t\'\'\'", \'unterminated triple-quoted t-string literal\'), ("t\'\'\'\'", \'unterminated triple-quoted t-string literal\'), ("t\'{", "\'{\' was never closed"), ("t\'{\'", "t-string: expecting \'}\'"), ("t\'{a\'", "t-string: expecting \'}\'"), ("t\'}\'", "t-string: single \'}\' is not allowed"), ("t\'{}\'", "t-string: valid expression required before \'}\'"), ("t\'{=x}\'", "t-string: valid expression required before \'=\'"), ("t\'{!x}\'", "t-string: valid expression required before \'!\'"), ("t\'{:x}\'", "t-string: valid expression required before \':\'"), ("t\'{x;y}\'", "t-string: expecting \'=\', or \'!\', or \':\', or \'}\'"), ("t\'{x=y}\'", "t-string: expecting \'!\', or \':\', or \'}\'"), ("t\'{x!s!}\'", "t-string: expecting \':\' or \'}\'"), ("t\'{x!s:\'", "t-string: expecting \'}\', or format specs"), ("t\'{x!}\'", \'t-string: missing conversion character\'), ("t\'{x=!}\'", \'t-string: missing conversion character\'), ("t\'{x!z}\'", "t-string: invalid conversion character \'z\': expected \'s\', \'r\', or \'a\'"), ("t\'{lambda:1}\'", \'t-string: lambda expressions are not allowed without parentheses\'), ("t\'{x:{;}}\'", "t-string: expecting a valid expression after \'{\'"), ("t\'{1:d\\n}\'", \'t-string: newlines are not allowed in format specifiers\')):\n    try: eval(source)\n    except SyntaxError as error:\n        assert message in str(error), (source, message, str(error))\n        print(source, message)\n    else: raise AssertionError(source)\n',
              "t' unterminated t-string literal\nt''' unterminated triple-quoted t-string literal\nt'''' unterminated triple-quoted t-string literal\nt'{ '{' was never closed\nt'{' t-string: expecting '}'\nt'{a' t-string: expecting '}'\nt'}' t-string: single '}' is not allowed\nt'{}' t-string: valid expression required before '}'\nt'{=x}' t-string: valid expression required before '='\nt'{!x}' t-string: valid expression required before '!'\nt'{:x}' t-string: valid expression required before ':'\nt'{x;y}' t-string: expecting '=', or '!', or ':', or '}'\nt'{x=y}' t-string: expecting '!', or ':', or '}'\nt'{x!s!}' t-string: expecting ':' or '}'\nt'{x!s:' t-string: expecting '}', or format specs\nt'{x!}' t-string: missing conversion character\nt'{x=!}' t-string: missing conversion character\nt'{x!z}' t-string: invalid conversion character 'z': expected 's', 'r', or 'a'\nt'{lambda:1}' t-string: lambda expressions are not allowed without parentheses\nt'{x:{;}}' t-string: expecting a valid expression after '{'\nt'{1:d\n}' t-string: newlines are not allowed in format specifiers\n")

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, ' x', None, ''),)) (3,) ('start{', Interpolation(3, ' x', None, ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, ' x', None, ''),)) (3,) ('start{', Interpolation(3, ' x', None, ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, ' x', None, '>8'),)) (3,) ('start{', Interpolation(3, ' x', None, '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x!r}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, ' x', 'r', ''),)) (3,) ('start{', Interpolation(3, ' x', 'r', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x!r:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, ' x', 'r', ''),)) (3,) ('start{', Interpolation(3, ' x', 'r', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x!r:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, ' x', 'r', '>8'),)) (3,) ('start{', Interpolation(3, ' x', 'r', '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x!s}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, ' x', 's', ''),)) (3,) ('start{', Interpolation(3, ' x', 's', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x!s:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, ' x', 's', ''),)) (3,) ('start{', Interpolation(3, ' x', 's', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x!s:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, ' x', 's', '>8'),)) (3,) ('start{', Interpolation(3, ' x', 's', '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x!a}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, ' x', 'a', ''),)) (3,) ('start{', Interpolation(3, ' x', 'a', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x!a:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, ' x', 'a', ''),)) (3,) ('start{', Interpolation(3, ' x', 'a', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x!a:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, ' x', 'a', '>8'),)) (3,) ('start{', Interpolation(3, ' x', 'a', '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{  x }}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, '  x ', None, ''),)) (3,) ('start{', Interpolation(3, '  x ', None, ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{  x :}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, '  x ', None, ''),)) (3,) ('start{', Interpolation(3, '  x ', None, ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{  x :>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, '  x ', None, '>8'),)) (3,) ('start{', Interpolation(3, '  x ', None, '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{  x !r}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, '  x ', 'r', ''),)) (3,) ('start{', Interpolation(3, '  x ', 'r', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{  x !r:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, '  x ', 'r', ''),)) (3,) ('start{', Interpolation(3, '  x ', 'r', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{  x !r:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, '  x ', 'r', '>8'),)) (3,) ('start{', Interpolation(3, '  x ', 'r', '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{  x !s}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, '  x ', 's', ''),)) (3,) ('start{', Interpolation(3, '  x ', 's', ''), '}end')
''')
