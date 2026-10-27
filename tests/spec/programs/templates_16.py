# spec: PLS-315 12.5, 23.7
# description: Programs on template strings and their malformed forms, each with the output CPython 3.15 gives.
from harness import *

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ (x := 4)!a:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(4, ' (x := 4)', 'a', '>8'),)) (4,) ('start{', Interpolation(4, ' (x := 4)', 'a', '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ (x,)}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation((3,), ' (x,)', None, ''),)) ((3,),) ('start{', Interpolation((3,), ' (x,)', None, ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ (x,):}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation((3,), ' (x,)', None, ''),)) ((3,),) ('start{', Interpolation((3,), ' (x,)', None, ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ (x,):>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation((3,), ' (x,)', None, '>8'),)) ((3,),) ('start{', Interpolation((3,), ' (x,)', None, '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ (x,)!r}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation((3,), ' (x,)', 'r', ''),)) ((3,),) ('start{', Interpolation((3,), ' (x,)', 'r', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ (x,)!r:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation((3,), ' (x,)', 'r', ''),)) ((3,),) ('start{', Interpolation((3,), ' (x,)', 'r', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ (x,)!r:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation((3,), ' (x,)', 'r', '>8'),)) ((3,),) ('start{', Interpolation((3,), ' (x,)', 'r', '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ (x,)!s}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation((3,), ' (x,)', 's', ''),)) ((3,),) ('start{', Interpolation((3,), ' (x,)', 's', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ (x,)!s:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation((3,), ' (x,)', 's', ''),)) ((3,),) ('start{', Interpolation((3,), ' (x,)', 's', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ (x,)!s:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation((3,), ' (x,)', 's', '>8'),)) ((3,),) ('start{', Interpolation((3,), ' (x,)', 's', '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ (x,)!a}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation((3,), ' (x,)', 'a', ''),)) ((3,),) ('start{', Interpolation((3,), ' (x,)', 'a', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ (x,)!a:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation((3,), ' (x,)', 'a', ''),)) ((3,),) ('start{', Interpolation((3,), ' (x,)', 'a', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ (x,)!a:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation((3,), ' (x,)', 'a', '>8'),)) ((3,),) ('start{', Interpolation((3,), ' (x,)', 'a', '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ {'a': x}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", None, ''),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", None, ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ {'a': x}:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", None, ''),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", None, ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ {'a': x}:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", None, '>8'),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", None, '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ {'a': x}!r}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", 'r', ''),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", 'r', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ {'a': x}!r:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", 'r', ''),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", 'r', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ {'a': x}!r:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", 'r', '>8'),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", 'r', '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ {'a': x}!s}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", 's', ''),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", 's', ''), '}end')
''')
