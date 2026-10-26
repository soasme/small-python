"""Check the test-only assertion adapter against the host regex implementation."""

import ast
import doctest
import io
from pathlib import Path
import random
import re
import sys
import tempfile

from run_cython import check_example, run_group


def main():
    root = Path(__file__).resolve().parent.parent
    # Compare the adapter with the actual upstream runner, including negative
    # controls. Doctest normalizes captured output, not the program's writes.
    output_examples = []
    for text in ['', 'x', 'x\n', 'x\n\n', '\n', 'x\r', 'αβ']:
        for want in [text, 'different\n']:
            output_examples.append(doctest.Example(f'print({text!r}, end="")\n', want))
    replies, error = run_group(Path(sys.argv[1]).resolve(), '', output_examples, 30)
    assert not error and replies[0]['ok'], (error, replies)
    for example, reply in zip(output_examples, replies[1:]):
        test = doctest.DocTest([example], {}, 'capture', '<capture>', 0, '')
        outcome = doctest.DocTestRunner().run(test, out=io.StringIO().write)
        assert check_example(example, reply) == (outcome.failed == 0), (example, reply)
    rng = random.Random(315)
    examples = []
    for _ in range(256):
        pattern = ''.join(rng.choice('ab') + rng.choice(('', '?')) for _ in range(rng.randrange(8)))
        text = ''.join(rng.choice('abc') for _ in range(rng.randrange(12)))
        expected = re.search(pattern, text) is not None
        examples.append(doctest.Example(
            f"assert unittest._pattern_matches(unittest._pattern_tokens({pattern!r}), {text!r}) is {expected}\n", ''))
    examples.append(doctest.Example('''
for pattern, text, expected in [('needle', 'a needle here', True), ('needle', 'other text', False)]:
    caught = False
    try:
        with unittest.TestCase().assertRaisesRegex(ValueError, pattern):
            raise ValueError(text)
    except AssertionError:
        caught = True
    assert caught is not expected
try:
    unittest.TestCase().assertRaisesRegex(ValueError, '.*')
except NotImplementedError:
    pass
else:
    raise AssertionError('unsupported regex was accepted')
events = []
class BrokenRepr:
    def __repr__(self): raise ValueError('repr')
class Cases(unittest.TestCase):
    def setUp(self): self.addCleanup(events.append, 'cleanup')
    def tearDown(self): events.append('teardown')
    def test_subtests(self):
        for i in range(3):
            with self.subTest(i=i):
                self.assertNotEqual(i, 1)
            events.append(i)
        with self.subTest(value=BrokenRepr()):
            self.assertTrue(True)
try:
    unittest._run_case(Cases, 'test_subtests')
except AssertionError as error:
    assert str(error) == '1 subtests failed'
else:
    raise AssertionError('subtest failure was lost')
assert events == [0, 1, 2, 'teardown', 'cleanup']
''', ''))
    replies, error = run_group(Path(sys.argv[1]).resolve(), 'import unittest\n', examples, 30, root / 'tests/support')
    if error or len(replies) != len(examples) + 1:
        raise AssertionError(error or 'missing framework results')
    for reply in replies:
        if not reply['ok']:
            raise AssertionError(reply)
    output = replies[-1]['output']
    records = ast.literal_eval(output.removeprefix('@spy-subtests@').strip())
    assert [record[2] for record in records] == ['passed', 'failed', 'passed', 'passed'], records
    assert [record[1] for record in records] == [{'i': '0'}, {'i': '1'}, {'i': '2'}, {'value': '<unrepresentable>'}], records
    for first_package in (False, True):
        for second_package in (False, True):
            with tempfile.TemporaryDirectory() as temp:
                paths = [Path(temp) / 'first', Path(temp) / 'second']
                for index, (path, package) in enumerate(zip(paths, [first_package, second_package])):
                    path.mkdir()
                    if package:
                        (path / 'fixture').mkdir()
                        target = path / 'fixture/__init__.py'
                    else:
                        target = path / 'fixture.py'
                    target.write_text(f'value = {index}\n')
                replies, error = run_group(Path(sys.argv[1]).resolve(), 'import fixture\nprint(fixture.value)\n', [], 10, paths)
                assert not error and replies[0]['ok'] and replies[0]['output'] == '0\n', (error, replies)
    print('Framework: 14 doctest captures, 256 regex-oracle comparisons, assertions, subtests, cleanup, and 4 module-path precedence checks passed')


if __name__ == '__main__':
    main()
