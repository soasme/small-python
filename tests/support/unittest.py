"""Test-only framework adaptation; never installed or embedded in the engine.

Upstream test modules import this implementation unchanged. Unsupported
framework operations fail explicitly. The oracle uses CPython's unittest.
"""


class SkipTest(Exception):
    pass


def _safe_repr(value):
    try:
        return repr(value)
    except Exception:
        return '<unrepresentable>'


def _pattern_tokens(pattern):
    # Literal characters, optional literals, and Unicode word boundaries.
    # Unsupported regex grammar must fail rather than weaken the assertion.
    if not isinstance(pattern, str):
        raise NotImplementedError('compiled regular expressions are not supported by the test framework')
    tokens = []
    index = 0
    while index < len(pattern):
        char = pattern[index]
        index += 1
        if char == '\\' and index < len(pattern) and pattern[index] == 'b':
            tokens.append((None, False))
            index += 1
            continue
        if char in '\\.^$*+{}[]|()':
            raise NotImplementedError('regular expression syntax is not supported by the test framework')
        if char == '?':
            if not tokens or tokens[-1][0] is None or tokens[-1][1]:
                raise NotImplementedError('regular expression syntax is not supported by the test framework')
            tokens[-1] = tokens[-1][0], True
        else:
            tokens.append((char, False))
    return tokens


def _pattern_matches(tokens, text):
    if all(char is not None and not optional for char, optional in tokens):
        return ''.join(char for char, optional in tokens) in text
    positions = [True] * (len(text) + 1)
    for char, optional in tokens:
        if char is None:
            for index in range(len(positions)):
                left = index > 0 and (text[index - 1].isalnum() or text[index - 1] == '_')
                right = index < len(text) and (text[index].isalnum() or text[index] == '_')
                positions[index] = positions[index] and left != right
            continue
        following = positions[:] if optional else [False] * len(positions)
        for index in range(len(text)):
            if positions[index] and text[index] == char:
                following[index + 1] = True
        positions = following
    return any(positions)


class _AssertRaises:
    def __init__(self, expected, pattern=None):
        self.expected = expected
        self.exception = None
        self.pattern = pattern
        self.tokens = _pattern_tokens(pattern) if pattern is not None else None

    def __enter__(self):
        return self

    def __exit__(self, kind, value, traceback):
        if kind is None:
            raise AssertionError('expected exception was not raised')
        if not issubclass(kind, self.expected):
            return False
        self.exception = value
        if self.tokens is not None:
            text = str(value)
            matches = _pattern_matches(self.tokens, text)
            if not matches:
                raise AssertionError(f'{self.pattern!r} does not match {text!r}')
        return True


class _SubTest:
    def __init__(self, case, message, params):
        self.case = case
        self.message = message
        self.params = dict(case._subtest_params)
        self.params.update(params)

    def __enter__(self):
        self.previous = self.case._subtest_params
        self.case._subtest_params = self.params
        self.failures = self.case._subtest_failures
        self.skips = self.case._subtest_skips

    def __exit__(self, kind, value, traceback):
        case = self.case
        case._subtest_params = self.previous
        if kind is not None and not issubclass(kind, Exception):
            return False
        if kind is not None:
            status = 'skipped' if issubclass(kind, SkipTest) else 'failed'
            if status == 'skipped': case._subtest_skips += 1
            else: case._subtest_failures += 1
            case._subtests.append((_safe_repr(self.message), {name: _safe_repr(item) for name, item in self.params.items()},
                                  status, kind.__name__, str(value)))
        elif case._subtest_failures == self.failures and case._subtest_skips == self.skips:
            case._subtests.append((_safe_repr(self.message), {name: _safe_repr(item) for name, item in self.params.items()},
                                  'passed', None, None))
        return True


class TestCase:
    def __init__(self, methodName='runTest'):
        self._testMethodName = methodName
        self._cleanups = []
        self._subtests = []
        self._subtest_params = {}
        self._subtest_failures = 0
        self._subtest_skips = 0

    def subTest(self, msg=None, **params):
        return _SubTest(self, msg, params)

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def addClassCleanup(cls, function, *args, **kwargs):
        cls._class_cleanups.append((function, args, kwargs))

    @classmethod
    def doClassCleanups(cls):
        while cls._class_cleanups:
            function, args, kwargs = cls._class_cleanups.pop()
            function(*args, **kwargs)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def addCleanup(self, function, *args, **kwargs):
        self._cleanups.append((function, args, kwargs))

    def doCleanups(self):
        while self._cleanups:
            function, args, kwargs = self._cleanups.pop()
            function(*args, **kwargs)

    def fail(self, msg=None):
        raise AssertionError(msg or 'test failed')

    def skipTest(self, reason):
        raise SkipTest(reason)

    def assertEqual(self, first, second, msg=None):
        if first != second:
            raise AssertionError(msg or f'{first!r} != {second!r}')

    def assertNotEqual(self, first, second, msg=None):
        if first == second:
            raise AssertionError(msg or f'{first!r} == {second!r}')

    def assertCountEqual(self, first, second, msg=None):
        first, second = list(first), list(second)
        try:
            counts = []
            for values in [first, second]:
                count = {}
                for value in values:
                    count[value] = count.get(value, 0) + 1
                counts.append(count)
        except TypeError:
            # CPython unittest.util._count_diff_all_purpose: compare and mark
            # each occurrence when elements cannot be dictionary keys.
            # See docs/licenses/python.txt.
            missing = object()
            for i, value in enumerate(first):
                if value is missing:
                    continue
                left = right = 0
                for j in range(i, len(first)):
                    if first[j] == value:
                        left += 1
                        first[j] = missing
                for j, other in enumerate(second):
                    if other == value:
                        right += 1
                        second[j] = missing
                if left != right:
                    self.fail(msg or 'element counts were not equal')
            if any(value is not missing for value in second):
                self.fail(msg or 'element counts were not equal')
        else:
            if counts[0] != counts[1]:
                self.fail(msg or 'element counts were not equal')

    def assertRegex(self, text, expected_regex, msg=None):
        if isinstance(expected_regex, str) and not expected_regex:
            self.fail('expected_regex must not be empty.')
        if not _pattern_matches(_pattern_tokens(expected_regex), text):
            self.fail(msg or f'{expected_regex!r} does not match {text!r}')

    def assertTrue(self, value, msg=None):
        if not value:
            raise AssertionError(msg or f'{value!r} is not true')

    def assertFalse(self, value, msg=None):
        if value:
            raise AssertionError(msg or f'{value!r} is not false')

    def assertIs(self, first, second, msg=None):
        if first is not second:
            raise AssertionError(msg or 'objects are not identical')

    def assertIsNot(self, first, second, msg=None):
        if first is second:
            raise AssertionError(msg or 'objects are identical')

    def assertIsNone(self, value, msg=None):
        self.assertIs(value, None, msg)

    def assertIsNotNone(self, value, msg=None):
        self.assertIsNot(value, None, msg)

    def assertIn(self, member, container, msg=None):
        if member not in container:
            raise AssertionError(msg or f'{member!r} not found')

    def assertNotIn(self, member, container, msg=None):
        if member in container:
            raise AssertionError(msg or f'{member!r} unexpectedly found')

    def assertIsInstance(self, value, types, msg=None):
        if not isinstance(value, types):
            raise AssertionError(msg or 'object has wrong type')

    def assertRaises(self, expected, *args, **kwargs):
        context = _AssertRaises(expected)
        if not args:
            return context
        with context:
            args[0](*args[1:], **kwargs)

    def assertRaisesRegex(self, expected, pattern, *args, **kwargs):
        context = _AssertRaises(expected, pattern)
        if not args:
            return context
        with context:
            args[0](*args[1:], **kwargs)


def _run_case(cls, name):
    case = cls(name)
    try:
        case.setUp()
        try:
            getattr(case, name)()
            if case._subtest_failures:
                raise AssertionError(f'{case._subtest_failures} subtests failed')
            if case._subtest_skips:
                raise SkipTest(f'{case._subtest_skips} subtests skipped')
        finally:
            case.tearDown()
    finally:
        try:
            case.doCleanups()
        finally:
            if case._subtests:
                print('@spy-subtests@' + repr(case._subtests))
