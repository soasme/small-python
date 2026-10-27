# spec: PLS-315 12.5, 23.7
# description: Programs on template strings and their malformed forms, each with the output CPython 3.15 gives.
from harness import *

check_program("x = 3\nwidth = 8\nv = T'''start{{{ (x,)!s:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation((3,), ' (x,)', 's', ''),)) ((3,),) ('start{', Interpolation((3,), ' (x,)', 's', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = T'''start{{{ (x,)!s:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation((3,), ' (x,)', 's', '>8'),)) ((3,),) ('start{', Interpolation((3,), ' (x,)', 's', '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = T'''start{{{ (x,)!a}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation((3,), ' (x,)', 'a', ''),)) ((3,),) ('start{', Interpolation((3,), ' (x,)', 'a', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = T'''start{{{ (x,)!a:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation((3,), ' (x,)', 'a', ''),)) ((3,),) ('start{', Interpolation((3,), ' (x,)', 'a', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = T'''start{{{ (x,)!a:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation((3,), ' (x,)', 'a', '>8'),)) ((3,),) ('start{', Interpolation((3,), ' (x,)', 'a', '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = T'''start{{{ {'a': x}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", None, ''),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", None, ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = T'''start{{{ {'a': x}:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", None, ''),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", None, ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = T'''start{{{ {'a': x}:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", None, '>8'),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", None, '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = T'''start{{{ {'a': x}!r}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", 'r', ''),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", 'r', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = T'''start{{{ {'a': x}!r:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", 'r', ''),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", 'r', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = T'''start{{{ {'a': x}!r:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", 'r', '>8'),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", 'r', '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = T'''start{{{ {'a': x}!s}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", 's', ''),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", 's', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = T'''start{{{ {'a': x}!s:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", 's', ''),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", 's', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = T'''start{{{ {'a': x}!s:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", 's', '>8'),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", 's', '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = T'''start{{{ {'a': x}!a}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", 'a', ''),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", 'a', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = T'''start{{{ {'a': x}!a:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", 'a', ''),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", 'a', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = T'''start{{{ {'a': x}!a:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", 'a', '>8'),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", 'a', '>8'), '}end')
''')

check_program('x = 3\nwidth = 8\nv = T\'\'\'start{{{ t"{x}"}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', None, ''),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', None, ''), '}end')
''')

check_program('x = 3\nwidth = 8\nv = T\'\'\'start{{{ t"{x}":}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', None, ''),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', None, ''), '}end')
''')

check_program('x = 3\nwidth = 8\nv = T\'\'\'start{{{ t"{x}":>{width}}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', None, '>8'),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', None, '>8'), '}end')
''')
