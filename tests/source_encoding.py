"""Source decoding against Python 3.15 and unchanged upstream methods.

The selected methods below require only unittest; their source is preserved.
This complements the complete test_utf8source port, not the unported modules.
"""

import ast
import difflib
import doctest
from pathlib import Path
import subprocess
import sys
import tempfile

from cpython import verify
from run_cython import run_group


def main():
    root = Path(__file__).resolve().parent.parent
    sys.path[:] = [entry for entry in sys.path if Path(entry).resolve() != root / 'tests']
    verify()
    engine = str(Path(sys.argv[1]).resolve())
    program = 'import unittest\n'
    examples = []
    for module, class_name, names in [
        ('test_source_encoding', 'MiscSourceEncodingTest', [
            'test_compilestring', 'test_issue4626', 'test_issue3297',
            'test_issue7820', 'test_truncated_utf8_at_eof']),
        ('test_compile', 'TestSpecifics', ['test_encoding']),
    ]:
        source = (root / f'tests/upstream/cpython/Lib/test/{module}.py').read_text()
        cls = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == class_name)
        methods = {n.name: n for n in cls.body if isinstance(n, ast.FunctionDef)}
        program += f'class {class_name}(unittest.TestCase):\n'
        for name in names:
            method = methods[name]
            assert not method.decorator_list, name
            program += ''.join(source.splitlines(keepends=True)[method.lineno - 1:method.end_lineno]) + '\n'
            examples.append(doctest.Example(f'{class_name}().{name}()\n', ''))
    oracle = subprocess.run([sys.executable, '-I', '-c', program + ''.join(e.source for e in examples)],
                            capture_output=True, text=True, timeout=30)
    assert oracle.returncode == 0, oracle.stderr
    replies, error = run_group(root / 'run-cython', program, examples, 30, root / 'tests/support')
    assert not error and len(replies) == len(examples) + 1 and all(r['ok'] for r in replies), (error, replies)

    sources = []
    for newline in [b'\n', b'\r\n', b'\r']:
        for prefix in [b'', b'\n', b'# comment\n', b'#!/usr/bin/env spy\n']:
            for encoding in ['utf-8', 'utf8', 'UTF_8', 'latin-1', 'latin1', 'ISO_LATIN_1', 'ascii']:
                codec = 'latin1' if encoding == 'ISO_LATIN_1' else encoding
                value = 'hello' if encoding == 'ascii' else 'Çα' if 'utf' in codec.lower() else 'Ç'
                for declaration in [f'# coding: {encoding}', f' \t# -*- coding={encoding} -*-']:
                    source = prefix + declaration.encode() + b'\nx = ' + repr(value).encode(codec) + b'\nprint(x)\n'
                    sources.append(source.replace(b'\n', newline))
    sources += [
        b'\xef\xbb\xbfprint("hello")', b'\xef\xbb\xbf# coding: UTF-8\nprint("hello")',
        b'x = 1\n# coding: fake\nprint(x)', b'\n\n# coding: fake\nprint(1)',
        b'print("""a\rb\r\nc""")', b'# coding: fake\n', b'# coding: ascii\nx="\xff"',
        b'# coding: latin-1\n\xc7 = "\xc7"\nprint(\xc7)',
        b'# coding: utf-8-extra\nprint("hello")', b'# coding: latin-1-extra\nprint("\xc7")',
        b'# coding: utf8\nprint("hello")\x00',
    ]
    checks = []
    for first in [' ', '        ', '\t', ' \t', '\t ', '\f\t']:
        for second in [' ', '        ', '\t', ' \t', '\t ', '\f\t']:
            for body in [f'if True:\n{first}print(1)\n{second}print(2)',
                         f'if True:\n{first}if True:\n{second}print(2)']:
                checks.append(f'''
try:
    exec({body!r})
except SyntaxError as error:
    print(type(error).__name__, error.msg, error.lineno)
''')
    for source in sources:
        for wrapper in ['bytes', 'bytearray']:
            for action in ['exec(source, {})', 'exec(compile(source, "source.py", "exec"), {})']:
                checks.append(f'''
source = {wrapper}({source!r})
try:
    {action}
except SyntaxError as error:
    print(type(error).__name__, error.msg, error.lineno, error.offset, error.text)
''')
    checks.append('''
class Text(str):
    def __str__(self): raise AssertionError('conversion hook')
class Bytes(bytes):
    def __bytes__(self): raise AssertionError('conversion hook')
for source in [Text('# coding: fake\\nprint("Ç")'), Bytes(b'print(7)'), bytearray(b'print(8)')]:
    exec(source)
    exec(compile(source, 'source.py', 'exec'))
for source in ['# coding: fake\\n"Ç"', b'# coding: latin-1\\n"\\xc7"', bytearray(b'6 * 7')]:
    print(eval(source))
for i in range(256):
    data = bytes([i])
    value = data.decode('iso8859-15')
    print(ascii(value), value.encode('iso-8859-15') == data)
for value in ['¤', '¦', '¨', '´', '¸', '¼', '½', '¾', 'α', '\\ud800']:
    for handler in ['strict', 'ignore', 'replace', 'backslashreplace', 'xmlcharrefreplace']:
        try: print(value.encode('iso8859-15', handler))
        except UnicodeEncodeError as error: print(str(error))
''')
    # Run many small examples in one process on each interpreter.
    source = '\n'.join(checks)
    expected = subprocess.run([sys.executable, '-I', '-c', source], capture_output=True, text=True, timeout=30)
    actual = subprocess.run([engine, '-c', source], capture_output=True, text=True, timeout=30)
    assert expected.returncode == actual.returncode == 0, (expected.stderr, actual.stderr)
    assert expected.stdout == actual.stdout, ''.join(difflib.unified_diff(
        expected.stdout.splitlines(keepends=True), actual.stdout.splitlines(keepends=True), 'CPython', 'spy'))
    # CLI and module loader must apply the same decoding to file bytes.
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory)
        (path / 'fixture.py').write_bytes(b'# coding: latin-1\r\nvalue = "\xc7"\r\n')
        (path / 'main.py').write_bytes(b'\xef\xbb\xbfimport fixture\rprint(fixture.value)\r')
        expected = subprocess.run([sys.executable, str(path / 'main.py')], capture_output=True, text=True, timeout=30)
        actual = subprocess.run([engine, str(path / 'main.py')], capture_output=True, text=True, timeout=30)
        assert expected.returncode == actual.returncode == 0 and expected.stdout == actual.stdout, (expected, actual)
    print(f'Source decoding: {len(examples)} unchanged upstream methods, {len(checks)} oracle checks, CLI and imports passed')


if __name__ == '__main__':
    main()
