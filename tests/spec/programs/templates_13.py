# spec: PLS-315 12.5, 23.7
# description: Programs on template strings and their malformed forms, each with the output CPython 3.15 gives.
from harness import *

check_program("x = 3\nwidth = 8\nv = rt'''start{{{ {'a': x}!a:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", 'a', '>8'),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", 'a', '>8'), '}end')
''')

check_program('x = 3\nwidth = 8\nv = rt\'\'\'start{{{ t"{x}"}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', None, ''),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', None, ''), '}end')
''')

check_program('x = 3\nwidth = 8\nv = rt\'\'\'start{{{ t"{x}":}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', None, ''),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', None, ''), '}end')
''')

check_program('x = 3\nwidth = 8\nv = rt\'\'\'start{{{ t"{x}":>{width}}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', None, '>8'),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', None, '>8'), '}end')
''')

check_program('x = 3\nwidth = 8\nv = rt\'\'\'start{{{ t"{x}"!r}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'r', ''),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'r', ''), '}end')
''')

check_program('x = 3\nwidth = 8\nv = rt\'\'\'start{{{ t"{x}"!r:}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'r', ''),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'r', ''), '}end')
''')

check_program('x = 3\nwidth = 8\nv = rt\'\'\'start{{{ t"{x}"!r:>{width}}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'r', '>8'),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'r', '>8'), '}end')
''')

check_program('x = 3\nwidth = 8\nv = rt\'\'\'start{{{ t"{x}"!s}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 's', ''),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 's', ''), '}end')
''')

check_program('x = 3\nwidth = 8\nv = rt\'\'\'start{{{ t"{x}"!s:}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 's', ''),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 's', ''), '}end')
''')

check_program('x = 3\nwidth = 8\nv = rt\'\'\'start{{{ t"{x}"!s:>{width}}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 's', '>8'),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 's', '>8'), '}end')
''')

check_program('x = 3\nwidth = 8\nv = rt\'\'\'start{{{ t"{x}"!a}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'a', ''),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'a', ''), '}end')
''')

check_program('x = 3\nwidth = 8\nv = rt\'\'\'start{{{ t"{x}"!a:}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'a', ''),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'a', ''), '}end')
''')

check_program('x = 3\nwidth = 8\nv = rt\'\'\'start{{{ t"{x}"!a:>{width}}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'a', '>8'),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'a', '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ x}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, ' x', None, ''),)) (3,) ('start{', Interpolation(3, ' x', None, ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ x:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, ' x', None, ''),)) (3,) ('start{', Interpolation(3, ' x', None, ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ x:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, ' x', None, '>8'),)) (3,) ('start{', Interpolation(3, ' x', None, '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ x!r}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, ' x', 'r', ''),)) (3,) ('start{', Interpolation(3, ' x', 'r', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ x!r:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, ' x', 'r', ''),)) (3,) ('start{', Interpolation(3, ' x', 'r', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ x!r:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, ' x', 'r', '>8'),)) (3,) ('start{', Interpolation(3, ' x', 'r', '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ x!s}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(3, ' x', 's', ''),)) (3,) ('start{', Interpolation(3, ' x', 's', ''), '}end')
''')
