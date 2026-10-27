# spec: PLS-315 12.5, 23.7
# description: Programs on template strings and their malformed forms, each with the output CPython 3.15 gives.
from harness import *

check_program("x = 3\nwidth = 8\nv = t'''start{{{  x !s:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, '  x ', 's', ''),)) (3,) ('start{', Interpolation(3, '  x ', 's', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{  x !s:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, '  x ', 's', '>8'),)) (3,) ('start{', Interpolation(3, '  x ', 's', '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{  x !a}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, '  x ', 'a', ''),)) (3,) ('start{', Interpolation(3, '  x ', 'a', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{  x !a:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, '  x ', 'a', ''),)) (3,) ('start{', Interpolation(3, '  x ', 'a', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{  x !a:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, '  x ', 'a', '>8'),)) (3,) ('start{', Interpolation(3, '  x ', 'a', '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x + 1}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(4, ' x + 1', None, ''),)) (4,) ('start{', Interpolation(4, ' x + 1', None, ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x + 1:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(4, ' x + 1', None, ''),)) (4,) ('start{', Interpolation(4, ' x + 1', None, ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x + 1:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(4, ' x + 1', None, '>8'),)) (4,) ('start{', Interpolation(4, ' x + 1', None, '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x + 1!r}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(4, ' x + 1', 'r', ''),)) (4,) ('start{', Interpolation(4, ' x + 1', 'r', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x + 1!r:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(4, ' x + 1', 'r', ''),)) (4,) ('start{', Interpolation(4, ' x + 1', 'r', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x + 1!r:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(4, ' x + 1', 'r', '>8'),)) (4,) ('start{', Interpolation(4, ' x + 1', 'r', '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x + 1!s}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(4, ' x + 1', 's', ''),)) (4,) ('start{', Interpolation(4, ' x + 1', 's', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x + 1!s:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(4, ' x + 1', 's', ''),)) (4,) ('start{', Interpolation(4, ' x + 1', 's', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x + 1!s:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(4, ' x + 1', 's', '>8'),)) (4,) ('start{', Interpolation(4, ' x + 1', 's', '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x + 1!a}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(4, ' x + 1', 'a', ''),)) (4,) ('start{', Interpolation(4, ' x + 1', 'a', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x + 1!a:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(4, ' x + 1', 'a', ''),)) (4,) ('start{', Interpolation(4, ' x + 1', 'a', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ x + 1!a:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(4, ' x + 1', 'a', '>8'),)) (4,) ('start{', Interpolation(4, ' x + 1', 'a', '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ (x := 4)}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(4, ' (x := 4)', None, ''),)) (4,) ('start{', Interpolation(4, ' (x := 4)', None, ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ (x := 4):}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(4, ' (x := 4)', None, ''),)) (4,) ('start{', Interpolation(4, ' (x := 4)', None, ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = t'''start{{{ (x := 4):>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(4, ' (x := 4)', None, '>8'),)) (4,) ('start{', Interpolation(4, ' (x := 4)', None, '>8'), '}end')
''')
