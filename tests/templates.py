"""Python 3.15 template-string differential checks, not whole-module ports.

Cases follow the pinned Lib/test/test_tstring.py and
Lib/test/test_string/test_templatelib.py contracts. The complete unchanged
modules remain separately accounted for by tests/cpython.py.
"""

from pathlib import Path
import ast
import itertools
import subprocess
import sys
import textwrap


def check(engine, source):
    source = textwrap.dedent(source)
    expected = subprocess.run([sys.executable, '-I', '-c', source], capture_output=True, text=True, timeout=30)
    actual = subprocess.run([engine, '-c', source], capture_output=True, text=True, timeout=30)
    if expected.returncode or actual.returncode or expected.stdout != actual.stdout:
        raise AssertionError(f'{source}\nCPython:\n{expected.stdout}{expected.stderr}\nspy:\n{actual.stdout}{actual.stderr}')


def main():
    if sys.version_info[:2] != (3, 15):
        raise SystemExit('Use the pinned Python 3.15 development oracle')
    engine = str(Path(sys.argv[1]).resolve())
    upstream = Path(__file__).parent / 'upstream/cpython/Lib/test/test_tstring.py'
    tree = ast.parse(upstream.read_text())
    syntax_test = next(node for node in ast.walk(tree)
                       if isinstance(node, ast.FunctionDef) and node.name == 'test_syntax_errors')
    syntax_cases = ast.literal_eval(syntax_test.body[0].iter)
    # Exercise every malformed source in the upstream table without changing
    # its source or expected diagnostic. This is a table port, not a module pass.
    check(engine, f'''
        for source, message in {syntax_cases!r}:
            try: eval(source)
            except SyntaxError as error:
                assert message in str(error), (source, message, str(error))
                print(source, message)
            else: raise AssertionError(source)
    ''')
    expressions = ['x', ' x ', 'x + 1', '(x := 4)', '(x,)', "{'a': x}", 't"{x}"']
    count = 0
    for prefix, expression, conversion, spec in itertools.product(
            ['t', 'T', 'rt', 'Tr'], expressions, ['', '!r', '!s', '!a'], ['', ':', ':>{width}']):
        literal = prefix + "'''start{{{ " + expression + conversion + spec + "}}}end'''"
        source = f'x = 3\nwidth = 8\nv = {literal}\nprint(v, v.values, tuple(v))\n'
        check(engine, source)
        count += 1
    check(engine, r'''
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
    ''')
    check(engine, r'''
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
    ''')
    check(engine, r'''
        events = []
        class Value:
            def __repr__(self): raise AssertionError('eager repr')
            def __str__(self): raise AssertionError('eager str')
            def __format__(self, spec): raise AssertionError('eager format')
        obj = Value()
        def value():
            events.append('value')
            return obj
        def width():
            events.append('width')
            return 8
        v = t'{value()!r:>{width()}}'
        print(events, v.interpolations[0].value is obj, v.interpolations[0].format_spec)
        x = 42
        for v in [t'{x=}', t'{ x = }', t'{x =!s}', t'{x=:04}', t'{x=!r:04}',
                  t"""{x =\
        }""", t"""{x =\
        !r}"""]:
            print(v)
        def generator():
            yield t'begin{(yield "value")!r:>{(yield "width")}}end'
        g = generator()
        print(next(g), g.send(42), g.send(5))
        try: next(g)
        except StopIteration: print('done')
        class Pause:
            def __await__(self):
                yield 'waiting'
                return 4
        async def coroutine():
            return t'{await Pause():>{await Pause()}}'
        iterator = coroutine().__await__()
        print(next(iterator), next(iterator))
        try: next(iterator)
        except StopIteration as error: print(error.value)
    ''')
    print(f'Templates: {count} literals, {len(syntax_cases)} upstream syntax cases, plus constructors, protocols, callbacks and suspension checks passed')


if __name__ == '__main__':
    main()
