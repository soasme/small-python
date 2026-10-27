# spec: PLS-315 12.5, 23.7
# description: Programs on template strings and their malformed forms, each with the output CPython 3.15 gives.
from harness import *

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ {'a': x}!s:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", 's', ''),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", 's', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ {'a': x}!s:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", 's', '>8'),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", 's', '>8'), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ {'a': x}!a}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", 'a', ''),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", 'a', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ {'a': x}!a:}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", 'a', ''),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", 'a', ''), '}end')
''')

check_program("x = 3\nwidth = 8\nv = Tr'''start{{{ {'a': x}!a:>{width}}}}end'''\nprint(v, v.values, tuple(v))\n",
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation({'a': 3}, " {'a': x}", 'a', '>8'),)) ({'a': 3},) ('start{', Interpolation({'a': 3}, " {'a': x}", 'a', '>8'), '}end')
''')

check_program('x = 3\nwidth = 8\nv = Tr\'\'\'start{{{ t"{x}"}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', None, ''),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', None, ''), '}end')
''')

check_program('x = 3\nwidth = 8\nv = Tr\'\'\'start{{{ t"{x}":}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', None, ''),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', None, ''), '}end')
''')

check_program('x = 3\nwidth = 8\nv = Tr\'\'\'start{{{ t"{x}":>{width}}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', None, '>8'),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', None, '>8'), '}end')
''')

check_program('x = 3\nwidth = 8\nv = Tr\'\'\'start{{{ t"{x}"!r}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'r', ''),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'r', ''), '}end')
''')

check_program('x = 3\nwidth = 8\nv = Tr\'\'\'start{{{ t"{x}"!r:}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'r', ''),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'r', ''), '}end')
''')

check_program('x = 3\nwidth = 8\nv = Tr\'\'\'start{{{ t"{x}"!r:>{width}}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'r', '>8'),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'r', '>8'), '}end')
''')

check_program('x = 3\nwidth = 8\nv = Tr\'\'\'start{{{ t"{x}"!s}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 's', ''),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 's', ''), '}end')
''')

check_program('x = 3\nwidth = 8\nv = Tr\'\'\'start{{{ t"{x}"!s:}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 's', ''),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 's', ''), '}end')
''')

check_program('x = 3\nwidth = 8\nv = Tr\'\'\'start{{{ t"{x}"!s:>{width}}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 's', '>8'),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 's', '>8'), '}end')
''')

check_program('x = 3\nwidth = 8\nv = Tr\'\'\'start{{{ t"{x}"!a}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'a', ''),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'a', ''), '}end')
''')

check_program('x = 3\nwidth = 8\nv = Tr\'\'\'start{{{ t"{x}"!a:}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'a', ''),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'a', ''), '}end')
''')

check_program('x = 3\nwidth = 8\nv = Tr\'\'\'start{{{ t"{x}"!a:>{width}}}}end\'\'\'\nprint(v, v.values, tuple(v))\n',
              '''Template(strings=('start{', '}end'), interpolations=(Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'a', '>8'),)) (Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)),) ('start{', Interpolation(Template(strings=('', ''), interpolations=(Interpolation(3, 'x', None, ''),)), ' t"{x}"', 'a', '>8'), '}end')
''')

check_program('''
Template = type(t'')
Interpolation = type(t'{0}'.interpolations[0])
class Text(str): pass
s = Text('abc')
for args in [(), ('hello',), ('a', 'b'), (Interpolation(1),),
             (Interpolation(1), Interpolation(2)), ('a', Interpolation(1), 'b'),
             (s,), (s, ''), ('', s)]:
    value = Template(*args)
    print(value, value.values, tuple(value), type(value.strings[0]).__name__, value.strings[0] is s)
for kwargs in [{}, {'expression': 'x'}, {'conversion': 'r'}, {'format_spec': '>4'},
               {'expression': s, 'conversion': Text('a'), 'format_spec': s}]:
    value = Interpolation(value=42, **kwargs)
    print(value, type(value.expression).__name__, type(value.conversion).__name__)
print(Template.__new__(Template, 'abc'))
print(Interpolation.__new__(Interpolation, 4))
for cls in [Template, Interpolation, type(iter(t''))]:
    print(cls.__name__, cls.__qualname__, cls.__module__)
    try:
        class Sub(cls): pass
    except TypeError: print('final')
x = []
value = t'{x}'
x.append(3)
print(value.values[0] is x, value.interpolations[0].value is x)
print(value != t'{x}', hash(value) == hash(value))
print(value.interpolations[0] != Interpolation(x))
for obj, names in [(value, ['strings', 'interpolations', 'values']),
                   (value.interpolations[0], ['value', 'expression', 'conversion', 'format_spec'])]:
    for name in names:
        try: setattr(obj, name, None)
        except AttributeError: print('readonly', name)
        try: delattr(obj, name)
        except AttributeError: print('cannot delete', name)
match value.interpolations[0]:
    case Interpolation(v, e, c, f): print(v, e, c, f)
for value in [t'', t'a', t'{1}', t'{1}{2}', t'a{1}b']:
    iterator = iter(value)
    print(iter(iterator) is iterator, tuple(iterator))
    for i in range(2):
        try: next(iterator)
        except StopIteration: print('exhausted')
    try: iterator.__next__()
    except StopIteration: print('exhausted method')
''',
              '''Template(strings=('',), interpolations=()) () () str False
Template(strings=('hello',), interpolations=()) () ('hello',) str False
Template(strings=('ab',), interpolations=()) () ('ab',) str False
Template(strings=('', ''), interpolations=(Interpolation(1, '', None, ''),)) (1,) (Interpolation(1, '', None, ''),) str False
Template(strings=('', '', ''), interpolations=(Interpolation(1, '', None, ''), Interpolation(2, '', None, ''))) (1, 2) (Interpolation(1, '', None, ''), Interpolation(2, '', None, '')) str False
Template(strings=('a', 'b'), interpolations=(Interpolation(1, '', None, ''),)) (1,) ('a', Interpolation(1, '', None, ''), 'b') str False
Template(strings=('abc',), interpolations=()) () ('abc',) Text True
Template(strings=('abc',), interpolations=()) () ('abc',) str False
Template(strings=('abc',), interpolations=()) () ('abc',) str False
Interpolation(42, '', None, '') str NoneType
Interpolation(42, 'x', None, '') str NoneType
Interpolation(42, '', 'r', '') str str
Interpolation(42, '', None, '>4') str NoneType
Interpolation(42, 'abc', 'a', 'abc') Text Text
Template(strings=('abc',), interpolations=())
Interpolation(4, '', None, '')
Template Template string.templatelib
final
Interpolation Interpolation string.templatelib
final
TemplateIter TemplateIter string.templatelib
final
True True
True True
True
readonly strings
cannot delete strings
readonly interpolations
cannot delete interpolations
readonly values
cannot delete values
readonly value
cannot delete value
readonly expression
cannot delete expression
readonly conversion
cannot delete conversion
readonly format_spec
cannot delete format_spec
[3] x None 
True ()
exhausted
exhausted
exhausted method
True ('a',)
exhausted
exhausted
exhausted method
True (Interpolation(1, '1', None, ''),)
exhausted
exhausted
exhausted method
True (Interpolation(1, '1', None, ''), Interpolation(2, '2', None, ''))
exhausted
exhausted
exhausted method
True ('a', Interpolation(1, '1', None, ''), 'b')
exhausted
exhausted
exhausted method
''')

check_program('''
Template = type(t'')
Interpolation = type(t'{0}'.interpolations[0])
for expression in ['Template(1)', 'Template(x=1)', 'Interpolation()',
                   'Interpolation(1, 2)', 'Interpolation(1, conversion=3)',
                   'Interpolation(1, conversion="")', 'Interpolation(1, conversion="z")',
                   'Interpolation(1, conversion="rr")', 'Interpolation(1, conversion=chr(0))',
                   'Interpolation(1, format_spec=None)', 'Interpolation(1, value=2)',
                   'Interpolation(1, x=2)', 'Interpolation(1, "", None, "", 2)']:
    try: eval(expression)
    except (TypeError, ValueError) as error: print(expression, type(error).__name__)
    else: raise AssertionError(expression)
for left in [t'', t'a', t'{1}', t'a{1}b']:
    for right in [t'', t'b', t'{2}', t'c{2}d']:
        combined = left + right
        print(combined, tuple(combined))
        print(combined is left, combined is right)
print(t'a' t'{1}' t'b', t'{2}' t'{3}')
for source in ['t"x" "x"', '"x" t"x"', 't"x" b"x"', 'b"x" t"x"',
               't"x" f"x"', 't"{"', 't"}"', 't"{}"', 't"{1!z}"', 'bt"x"']:
    try: eval(source)
    except SyntaxError: print('syntax', source)
    else: raise AssertionError(source)
for source in ['t"" + ""', '"" + t""']:
    try: eval(source)
    except TypeError as error: print(error)
''',
              '''Template(1) TypeError
Template(x=1) TypeError
Interpolation() TypeError
Interpolation(1, 2) TypeError
Interpolation(1, conversion=3) TypeError
Interpolation(1, conversion="") ValueError
Interpolation(1, conversion="z") ValueError
Interpolation(1, conversion="rr") ValueError
Interpolation(1, conversion=chr(0)) ValueError
Interpolation(1, format_spec=None) TypeError
Interpolation(1, value=2) TypeError
Interpolation(1, x=2) TypeError
Interpolation(1, "", None, "", 2) TypeError
Template(strings=('',), interpolations=()) ()
False False
Template(strings=('b',), interpolations=()) ('b',)
False False
Template(strings=('', ''), interpolations=(Interpolation(2, '2', None, ''),)) (Interpolation(2, '2', None, ''),)
False False
Template(strings=('c', 'd'), interpolations=(Interpolation(2, '2', None, ''),)) ('c', Interpolation(2, '2', None, ''), 'd')
False False
Template(strings=('a',), interpolations=()) ('a',)
False False
Template(strings=('ab',), interpolations=()) ('ab',)
False False
Template(strings=('a', ''), interpolations=(Interpolation(2, '2', None, ''),)) ('a', Interpolation(2, '2', None, ''))
False False
Template(strings=('ac', 'd'), interpolations=(Interpolation(2, '2', None, ''),)) ('ac', Interpolation(2, '2', None, ''), 'd')
False False
Template(strings=('', ''), interpolations=(Interpolation(1, '1', None, ''),)) (Interpolation(1, '1', None, ''),)
False False
Template(strings=('', 'b'), interpolations=(Interpolation(1, '1', None, ''),)) (Interpolation(1, '1', None, ''), 'b')
False False
Template(strings=('', '', ''), interpolations=(Interpolation(1, '1', None, ''), Interpolation(2, '2', None, ''))) (Interpolation(1, '1', None, ''), Interpolation(2, '2', None, ''))
False False
Template(strings=('', 'c', 'd'), interpolations=(Interpolation(1, '1', None, ''), Interpolation(2, '2', None, ''))) (Interpolation(1, '1', None, ''), 'c', Interpolation(2, '2', None, ''), 'd')
False False
Template(strings=('a', 'b'), interpolations=(Interpolation(1, '1', None, ''),)) ('a', Interpolation(1, '1', None, ''), 'b')
False False
Template(strings=('a', 'bb'), interpolations=(Interpolation(1, '1', None, ''),)) ('a', Interpolation(1, '1', None, ''), 'bb')
False False
Template(strings=('a', 'b', ''), interpolations=(Interpolation(1, '1', None, ''), Interpolation(2, '2', None, ''))) ('a', Interpolation(1, '1', None, ''), 'b', Interpolation(2, '2', None, ''))
False False
Template(strings=('a', 'bc', 'd'), interpolations=(Interpolation(1, '1', None, ''), Interpolation(2, '2', None, ''))) ('a', Interpolation(1, '1', None, ''), 'bc', Interpolation(2, '2', None, ''), 'd')
False False
Template(strings=('a', 'b'), interpolations=(Interpolation(1, '1', None, ''),)) Template(strings=('', '', ''), interpolations=(Interpolation(2, '2', None, ''), Interpolation(3, '3', None, '')))
syntax t"x" "x"
syntax "x" t"x"
syntax t"x" b"x"
syntax b"x" t"x"
syntax t"x" f"x"
syntax t"{"
syntax t"}"
syntax t"{}"
syntax t"{1!z}"
syntax bt"x"
can only concatenate string.templatelib.Template (not "str") to string.templatelib.Template
can only concatenate str (not "string.templatelib.Template") to str
''')

check_program('\nevents = []\nclass Value:\n    def __repr__(self): raise AssertionError(\'eager repr\')\n    def __str__(self): raise AssertionError(\'eager str\')\n    def __format__(self, spec): raise AssertionError(\'eager format\')\nobj = Value()\ndef value():\n    events.append(\'value\')\n    return obj\ndef width():\n    events.append(\'width\')\n    return 8\nv = t\'{value()!r:>{width()}}\'\nprint(events, v.interpolations[0].value is obj, v.interpolations[0].format_spec)\nx = 42\nfor v in [t\'{x=}\', t\'{ x = }\', t\'{x =!s}\', t\'{x=:04}\', t\'{x=!r:04}\',\n          t"""{x =\\\n}""", t"""{x =\\\n!r}"""]:\n    print(v)\ndef generator():\n    yield t\'begin{(yield "value")!r:>{(yield "width")}}end\'\ng = generator()\nprint(next(g), g.send(42), g.send(5))\ntry: next(g)\nexcept StopIteration: print(\'done\')\nclass Pause:\n    def __await__(self):\n        yield \'waiting\'\n        return 4\nasync def coroutine():\n    return t\'{await Pause():>{await Pause()}}\'\niterator = coroutine().__await__()\nprint(next(iterator), next(iterator))\ntry: next(iterator)\nexcept StopIteration as error: print(error.value)\n',
              '[\'value\', \'width\'] True >8\nTemplate(strings=(\'x=\', \'\'), interpolations=(Interpolation(42, \'x\', \'r\', \'\'),))\nTemplate(strings=(\' x = \', \'\'), interpolations=(Interpolation(42, \' x \', \'r\', \'\'),))\nTemplate(strings=(\'x =\', \'\'), interpolations=(Interpolation(42, \'x \', \'s\', \'\'),))\nTemplate(strings=(\'x=\', \'\'), interpolations=(Interpolation(42, \'x\', None, \'04\'),))\nTemplate(strings=(\'x=\', \'\'), interpolations=(Interpolation(42, \'x\', \'r\', \'04\'),))\nTemplate(strings=(\'x =\\\\\\n\', \'\'), interpolations=(Interpolation(42, \'x \', \'r\', \'\'),))\nTemplate(strings=(\'x =\\\\\\n\', \'\'), interpolations=(Interpolation(42, \'x \', \'r\', \'\'),))\nvalue width Template(strings=(\'begin\', \'end\'), interpolations=(Interpolation(42, \'(yield "value")\', \'r\', \'>5\'),))\ndone\nwaiting waiting\nTemplate(strings=(\'\', \'\'), interpolations=(Interpolation(4, \'await Pause()\', None, \'>4\'),))\n')
