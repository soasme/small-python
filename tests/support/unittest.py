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


class _Unsupported(NotImplementedError):
    pass


def _unsupported(what):
    raise _Unsupported(f'regular expression {what} is not supported by the test framework')


# A backtracking subset of re.search for str patterns without flags: literals
# and escapes, '.', classes, anchors (^ $ \A \Z \b \B), groups, alternation,
# and greedy or lazy quantifiers. Other syntax fails rather than weakening an
# assertion. Character categories follow re's Unicode str definitions.
def _word(char):
    return char.isalnum() or char == '_'


_CATEGORIES = {
    'd': lambda char: char.isdecimal(), 'D': lambda char: not char.isdecimal(),
    'w': _word, 'W': lambda char: not _word(char),
    's': lambda char: char.isspace(), 'S': lambda char: not char.isspace(),
}
_ESCAPES = {'n': '\n', 't': '\t', 'r': '\r', 'f': '\f', 'v': '\v', 'a': '\a', '0': '\0'}


class _Parser:
    def __init__(self, pattern):
        self.pattern = pattern
        self.index = 0

    def peek(self):
        return self.pattern[self.index] if self.index < len(self.pattern) else None

    def take(self):
        char = self.peek()
        self.index += 1
        return char

    def alternation(self):
        branches = [self.sequence()]
        while self.peek() == '|':
            self.take()
            branches.append(self.sequence())
        return ('alt', branches) if len(branches) > 1 else branches[0]

    def sequence(self):
        items = []
        while self.peek() is not None and self.peek() not in '|)':
            atom = self.atom()
            items.append(self.quantified(atom))
        return ('seq', items)

    def quantified(self, atom):
        char = self.peek()
        if char is None or char not in '*+?{':
            return atom
        if char == '{':
            bounds = self.bounds()
            if bounds is None:
                return atom
            low, high = bounds
        else:
            self.take()
            low, high = {'*': (0, None), '+': (1, None), '?': (0, 1)}[char]
        if atom[0] in ('bol', 'eol', 'start', 'end', 'boundary', 'nonboundary', 'repeat'):
            _unsupported('repetition of this item')
        lazy = self.peek() == '?'
        if lazy:
            self.take()
        elif self.peek() == '+':
            _unsupported('possessive quantifiers')
        return ('repeat', atom, low, high, lazy)

    def bounds(self):
        # sre_parse: {m}, {m,}, {,n}, {m,n} or {,}; otherwise a literal brace.
        index = self.index + 1
        low = high = ''
        while index < len(self.pattern) and self.pattern[index] in '0123456789':
            low += self.pattern[index]
            index += 1
        comma = index < len(self.pattern) and self.pattern[index] == ','
        if comma:
            index += 1
            while index < len(self.pattern) and self.pattern[index] in '0123456789':
                high += self.pattern[index]
                index += 1
        if index >= len(self.pattern) or self.pattern[index] != '}' or index == self.index + 1:
            return None
        self.index = index + 1
        low_value = int(low) if low else 0
        high_value = int(high) if high else (None if comma else low_value)
        if high_value is not None and high_value < low_value:
            _unsupported('bounds')
        return low_value, high_value

    def atom(self):
        char = self.take()
        if char == '(':
            if self.peek() == '?':
                self.take()
                kind = self.take()
                if kind == 'P' and self.peek() == '<':
                    end = self.pattern.find('>', self.index)
                    if end < 0:
                        _unsupported('group names')
                    self.index = end + 1
                elif kind != ':':
                    _unsupported('extensions')
            inner = self.alternation()
            if self.take() != ')':
                _unsupported('unbalanced parentheses')
            return ('group', inner)
        if char == ')':
            _unsupported('unbalanced parentheses')
        if char == '[':
            return self.charclass()
        if char == '.':
            return ('char', lambda value: value != '\n')
        if char == '^':
            return ('bol',)
        if char == '$':
            return ('eol',)
        if char in '*+?':
            _unsupported('repetition without an item')
        if char == '{' and self.bounds_follow():
            _unsupported('repetition without an item')
        if char == '\\':
            return self.escape(False)
        return ('literal', char)

    def bounds_follow(self):
        save = self.index
        self.index -= 1
        result = self.bounds() is not None
        self.index = save
        return result

    def escape(self, in_class):
        char = self.take()
        if char is None:
            _unsupported('trailing backslash')
        if char in _CATEGORIES:
            return ('char', _CATEGORIES[char])
        if not in_class and char in 'AZbB':
            return {'A': ('start',), 'Z': ('end',), 'b': ('boundary',), 'B': ('nonboundary',)}[char]
        if char in _ESCAPES and not (char == '0' and self.peek() is not None and self.peek() in '01234567'):
            return ('literal', _ESCAPES[char])
        if char in 'xuU':
            width = {'x': 2, 'u': 4, 'U': 8}[char]
            digits = self.pattern[self.index:self.index + width]
            if len(digits) != width or not all(d in '0123456789abcdefABCDEF' for d in digits):
                _unsupported('escapes')
            self.index += width
            return ('literal', chr(int(digits, 16)))
        if char.isalnum():
            _unsupported('escapes')
        return ('literal', char)

    def charclass(self):
        negate = self.peek() == '^'
        if negate:
            self.take()
        tests = []
        first = True
        while True:
            char = self.take()
            if char is None:
                _unsupported('unterminated character sets')
            if char == ']' and not first:
                break
            first = False
            if char == '[' and self.peek() in (':', '=', '.'):
                _unsupported('POSIX classes')
            if char == '\\':
                item = self.escape(True)
                if item[0] == 'char':
                    tests.append(item[1])
                    continue
                low = item[1]
            else:
                low = char
            if self.peek() == '-' and self.index + 1 < len(self.pattern) and self.pattern[self.index + 1] != ']':
                self.take()
                high = self.take()
                if high == '\\':
                    item = self.escape(True)
                    if item[0] == 'char':
                        _unsupported('ranges')
                    high = item[1]
                if ord(high) < ord(low):
                    _unsupported('ranges')
                tests.append(lambda value, low=low, high=high: low <= value <= high)
            else:
                tests.append(lambda value, low=low: value == low)
        if negate:
            return ('char', lambda value: not any(test(value) for test in tests))
        return ('char', lambda value: any(test(value) for test in tests))


def _compile(pattern):
    if not isinstance(pattern, str):
        raise _Unsupported('compiled regular expressions are not supported by the test framework')
    parser = _Parser(pattern)
    tree = parser.alternation()
    if parser.index != len(pattern):
        _unsupported('unbalanced parentheses')
    return tree


def _single(node):
    # A node matching exactly one character, as a predicate.
    if node[0] == 'literal':
        char = node[1]
        return lambda value: value == char
    if node[0] == 'char':
        return node[1]
    return None


def _match(node, text, index, cont):
    kind = node[0]
    if kind == 'seq':
        return _match_seq(node[1], 0, text, index, cont)
    if kind == 'literal' or kind == 'char':
        if index < len(text) and _single(node)(text[index]):
            return cont(index + 1)
        return False
    if kind == 'alt':
        return any(_match(branch, text, index, cont) for branch in node[1])
    if kind == 'group':
        return _match(node[1], text, index, cont)
    if kind == 'bol' or kind == 'start':
        return index == 0 and cont(index)
    if kind == 'end':
        return index == len(text) and cont(index)
    if kind == 'eol':
        return (index == len(text) or index == len(text) - 1 and text[index] == '\n') and cont(index)
    if kind == 'boundary' or kind == 'nonboundary':
        left = index > 0 and _word(text[index - 1])
        right = index < len(text) and _word(text[index])
        return ((left != right) == (kind == 'boundary')) and cont(index)
    _, item, low, high, lazy = node
    test = _single(item)
    if test is not None:
        # Single characters repeat iteratively; backtracking only shortens.
        limit = index
        while limit < len(text) and (high is None or limit - index < high) and test(text[limit]):
            limit += 1
        if limit - index < low:
            return False
        ends = range(index + low, limit + 1) if lazy else range(limit, index + low - 1, -1)
        return any(cont(end) for end in ends)
    return _repeat(item, low, high, lazy, text, index, cont, 0)


def _repeat(item, low, high, lazy, text, index, cont, count):
    def more(end):
        # Past the minimum, an empty iteration ends the repeat, as in sre.
        return (end != index or count < low) and _repeat(item, low, high, lazy, text, end, cont, count + 1)
    can_stop = count >= low
    can_continue = high is None or count < high
    if lazy:
        return (can_stop and cont(index)) or (can_continue and _match(item, text, index, more))
    return (can_continue and _match(item, text, index, more)) or (can_stop and cont(index))


def _match_seq(items, position, text, index, cont):
    if position == len(items):
        return cont(index)
    return _match(items[position], text, index,
                  lambda end: _match_seq(items, position + 1, text, end, cont))


def _search(pattern, text):
    tree = _compile(pattern)
    return any(_match(tree, text, start, lambda end: True) for start in range(len(text) + 1))


class _AssertRaises:
    def __init__(self, case, expected, pattern=None, msg=None):
        if not (isinstance(expected, type) and issubclass(expected, BaseException) or
                isinstance(expected, tuple) and expected and
                all(isinstance(e, type) and issubclass(e, BaseException) for e in expected)):
            raise TypeError('assertRaises() arg 1 must be an exception type or tuple of exception types')
        self.case = case
        self.expected = expected
        self.exception = None
        self.pattern = pattern
        self.msg = msg
        if pattern is not None:
            _compile(pattern)

    def __enter__(self):
        return self

    def __exit__(self, kind, value, traceback):
        if kind is None:
            name = getattr(self.expected, '__name__', str(self.expected))
            self.case.fail(self.case._formatMessage(self.msg, f'{name} not raised'))
        if not issubclass(kind, self.expected):
            return False
        self.exception = value
        if self.pattern is not None:
            text = str(value)
            if not _search(self.pattern, text):
                self.case.fail(self.case._formatMessage(self.msg, f'{self.pattern!r} does not match {text!r}'))
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


def _id(obj):
    return obj


def skip(reason):
    """Unconditionally skip a test."""
    def decorator(test_item):
        test_item.__unittest_skip__ = True
        test_item.__unittest_skip_why__ = reason
        return test_item
    if isinstance(reason, type(_id)):
        test_item = reason
        reason = ''
        return decorator(test_item)
    return decorator


def skipIf(condition, reason):
    """Skip a test if the condition is true."""
    if condition:
        return skip(reason)
    return _id


def skipUnless(condition, reason):
    """Skip a test unless the condition is true."""
    if not condition:
        return skip(reason)
    return _id


def expectedFailure(test_item):
    test_item.__unittest_expecting_failure__ = True
    return test_item


class TestCase:
    failureException = AssertionError
    longMessage = True
    maxDiff = 80 * 8
    _class_cleanups = []

    def __init__(self, methodName='runTest'):
        self._testMethodName = methodName
        self._cleanups = []
        self._subtests = []
        self._subtest_params = {}
        self._subtest_failures = 0
        self._subtest_skips = 0
        self._type_equality_funcs = {}
        self.addTypeEqualityFunc(dict, 'assertDictEqual')
        self.addTypeEqualityFunc(list, 'assertListEqual')
        self.addTypeEqualityFunc(tuple, 'assertTupleEqual')
        self.addTypeEqualityFunc(set, 'assertSetEqual')
        self.addTypeEqualityFunc(frozenset, 'assertSetEqual')
        self.addTypeEqualityFunc(str, 'assertMultiLineEqual')

    def addTypeEqualityFunc(self, typeobj, function):
        self._type_equality_funcs[typeobj] = function

    def id(self):
        return f'{type(self).__module__}.{type(self).__qualname__}.{self._testMethodName}'

    def __str__(self):
        return f'{self._testMethodName} ({type(self).__module__}.{type(self).__qualname__})'

    def __repr__(self):
        return f'<{type(self).__module__}.{type(self).__qualname__} testMethod={self._testMethodName}>'

    def shortDescription(self):
        doc = getattr(self, self._testMethodName).__doc__
        return doc.strip().split("\n")[0].strip() if doc else None

    def subTest(self, msg=None, **params):
        return _SubTest(self, msg, params)

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def addClassCleanup(cls, function, /, *args, **kwargs):
        cls._class_cleanups.append((function, args, kwargs))

    @classmethod
    def doClassCleanups(cls):
        while cls._class_cleanups:
            function, args, kwargs = cls._class_cleanups.pop()
            function(*args, **kwargs)

    @classmethod
    def enterClassContext(cls, cm):
        result = type(cm).__enter__(cm)
        cls.addClassCleanup(type(cm).__exit__, cm, None, None, None)
        return result

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def addCleanup(self, function, /, *args, **kwargs):
        self._cleanups.append((function, args, kwargs))

    def enterContext(self, cm):
        result = type(cm).__enter__(cm)
        self.addCleanup(type(cm).__exit__, cm, None, None, None)
        return result

    def doCleanups(self):
        while self._cleanups:
            function, args, kwargs = self._cleanups.pop()
            function(*args, **kwargs)

    def _formatMessage(self, msg, standardMsg):
        if not self.longMessage:
            return msg or standardMsg
        if msg is None:
            return standardMsg
        return f'{standardMsg} : {msg}'

    def fail(self, msg=None):
        raise self.failureException(msg)

    def skipTest(self, reason):
        raise SkipTest(reason)

    def _getAssertEqualityFunc(self, first, second):
        if type(first) == type(second):
            asserter = self._type_equality_funcs.get(type(first))
            if asserter is not None:
                if isinstance(asserter, str):
                    asserter = getattr(self, asserter)
                return asserter
        return self._baseAssertEqual

    def _baseAssertEqual(self, first, second, msg=None):
        if not first == second:
            self.fail(self._formatMessage(msg, f'{_safe_repr(first)} != {_safe_repr(second)}'))

    def assertEqual(self, first, second, msg=None):
        assertion_func = self._getAssertEqualityFunc(first, second)
        assertion_func(first, second, msg=msg)

    def assertNotEqual(self, first, second, msg=None):
        if not first != second:
            self.fail(self._formatMessage(msg, f'{_safe_repr(first)} == {_safe_repr(second)}'))

    def assertAlmostEqual(self, first, second, places=None, msg=None, delta=None):
        if first == second:
            return
        if delta is not None and places is not None:
            raise TypeError("specify delta or places not both")
        diff = abs(first - second)
        if delta is not None:
            if diff <= delta:
                return
            standardMsg = f'{_safe_repr(first)} != {_safe_repr(second)} within {_safe_repr(delta)} delta ({_safe_repr(diff)} difference)'
        else:
            if places is None:
                places = 7
            if round(diff, places) == 0:
                return
            standardMsg = f'{_safe_repr(first)} != {_safe_repr(second)} within {places!r} places ({_safe_repr(diff)} difference)'
        self.fail(self._formatMessage(msg, standardMsg))

    def assertNotAlmostEqual(self, first, second, places=None, msg=None, delta=None):
        if delta is not None and places is not None:
            raise TypeError("specify delta or places not both")
        diff = abs(first - second)
        if delta is not None:
            if not (first == second) and diff > delta:
                return
            standardMsg = f'{_safe_repr(first)} == {_safe_repr(second)} within {_safe_repr(delta)} delta ({_safe_repr(diff)} difference)'
        else:
            if places is None:
                places = 7
            if not (first == second) and round(diff, places) != 0:
                return
            standardMsg = f'{_safe_repr(first)} == {_safe_repr(second)} within {places!r} places'
        self.fail(self._formatMessage(msg, standardMsg))

    def assertSequenceEqual(self, seq1, seq2, msg=None, seq_type=None):
        if seq_type is not None:
            seq_type_name = seq_type.__name__
            if not isinstance(seq1, seq_type):
                self.fail(self._formatMessage(msg, f'First sequence is not a {seq_type_name}: {_safe_repr(seq1)}'))
            if not isinstance(seq2, seq_type):
                self.fail(self._formatMessage(msg, f'Second sequence is not a {seq_type_name}: {_safe_repr(seq2)}'))
        else:
            seq_type_name = "sequence"
        try:
            len(seq1)
        except (TypeError, NotImplementedError):
            self.fail(self._formatMessage(msg, f'First {seq_type_name} has no length.    Non-sequence?'))
        try:
            len(seq2)
        except (TypeError, NotImplementedError):
            self.fail(self._formatMessage(msg, f'Second {seq_type_name} has no length.    Non-sequence?'))
        if seq1 == seq2:
            return
        self.fail(self._formatMessage(msg, f'{seq_type_name.capitalize()}s differ: {_safe_repr(seq1)} != {_safe_repr(seq2)}'))

    def assertListEqual(self, list1, list2, msg=None):
        self.assertSequenceEqual(list1, list2, msg, seq_type=list)

    def assertTupleEqual(self, tuple1, tuple2, msg=None):
        self.assertSequenceEqual(tuple1, tuple2, msg, seq_type=tuple)

    def assertSetEqual(self, set1, set2, msg=None):
        try:
            difference1 = set1.difference(set2)
        except TypeError as e:
            self.fail(f'invalid type when attempting set difference: {e}')
        except AttributeError as e:
            self.fail(f'first argument does not support set difference: {e}')
        try:
            difference2 = set2.difference(set1)
        except TypeError as e:
            self.fail(f'invalid type when attempting set difference: {e}')
        except AttributeError as e:
            self.fail(f'second argument does not support set difference: {e}')
        if not (difference1 or difference2):
            return
        self.fail(self._formatMessage(msg, f'Items in the first set but not the second: {difference1!r}; '
                                           f'items in the second set but not the first: {difference2!r}'))

    def assertDictEqual(self, d1, d2, msg=None):
        self.assertIsInstance(d1, dict, 'First argument is not a dictionary')
        self.assertIsInstance(d2, dict, 'Second argument is not a dictionary')
        if d1 != d2:
            self.fail(self._formatMessage(msg, f'{_safe_repr(d1)} != {_safe_repr(d2)}'))

    def assertMultiLineEqual(self, first, second, msg=None):
        self.assertIsInstance(first, str, "First argument is not a string")
        self.assertIsInstance(second, str, "Second argument is not a string")
        if first != second:
            self.fail(self._formatMessage(msg, f'{_safe_repr(first)} != {_safe_repr(second)}'))

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
        if not _search(expected_regex, text):
            self.fail(self._formatMessage(msg, f"Regex didn't match: {expected_regex!r} not found in {text!r}"))

    def assertNotRegex(self, text, unexpected_regex, msg=None):
        if _search(unexpected_regex, text):
            self.fail(self._formatMessage(msg, f'Regex matched: {unexpected_regex!r} found in {text!r}'))

    def assertTrue(self, expr, msg=None):
        if not expr:
            self.fail(self._formatMessage(msg, f'{_safe_repr(expr)} is not true'))

    def assertFalse(self, expr, msg=None):
        if expr:
            self.fail(self._formatMessage(msg, f'{_safe_repr(expr)} is not false'))

    def assertIs(self, expr1, expr2, msg=None):
        if expr1 is not expr2:
            self.fail(self._formatMessage(msg, f'{_safe_repr(expr1)} is not {_safe_repr(expr2)}'))

    def assertIsNot(self, expr1, expr2, msg=None):
        if expr1 is expr2:
            self.fail(self._formatMessage(msg, f'unexpectedly identical: {_safe_repr(expr1)}'))

    def assertIsNone(self, obj, msg=None):
        if obj is not None:
            self.fail(self._formatMessage(msg, f'{_safe_repr(obj)} is not None'))

    def assertIsNotNone(self, obj, msg=None):
        if obj is None:
            self.fail(self._formatMessage(msg, 'unexpectedly None'))

    def assertIn(self, member, container, msg=None):
        if member not in container:
            self.fail(self._formatMessage(msg, f'{_safe_repr(member)} not found in {_safe_repr(container)}'))

    def assertNotIn(self, member, container, msg=None):
        if member in container:
            self.fail(self._formatMessage(msg, f'{_safe_repr(member)} unexpectedly found in {_safe_repr(container)}'))

    def assertIsInstance(self, obj, cls, msg=None):
        if not isinstance(obj, cls):
            self.fail(self._formatMessage(msg, f'{_safe_repr(obj)} is not an instance of {cls!r}'))

    def assertNotIsInstance(self, obj, cls, msg=None):
        if isinstance(obj, cls):
            self.fail(self._formatMessage(msg, f'{_safe_repr(obj)} is an instance of {cls!r}'))

    def assertIsSubclass(self, cls, superclass, msg=None):
        try:
            if issubclass(cls, superclass):
                return
        except TypeError:
            if not isinstance(cls, type):
                self.fail(self._formatMessage(msg, f'{cls!r} is not a class'))
            raise
        self.fail(self._formatMessage(msg, f'{cls!r} is not a subclass of {superclass!r}'))

    def assertNotIsSubclass(self, cls, superclass, msg=None):
        try:
            if not issubclass(cls, superclass):
                return
        except TypeError:
            if not isinstance(cls, type):
                self.fail(self._formatMessage(msg, f'{cls!r} is not a class'))
            raise
        self.fail(self._formatMessage(msg, f'{cls!r} is a subclass of {superclass!r}'))

    def assertHasAttr(self, obj, name, msg=None):
        if not hasattr(obj, name):
            self.fail(self._formatMessage(msg, f'{_safe_repr(obj)} has no attribute {name!r}'))

    def assertNotHasAttr(self, obj, name, msg=None):
        if hasattr(obj, name):
            self.fail(self._formatMessage(msg, f'{_safe_repr(obj)} has unexpected attribute {name!r}'))

    def assertStartsWith(self, s, prefix, msg=None):
        try:
            if s.startswith(prefix):
                return
        except (AttributeError, TypeError):
            self.fail(self._formatMessage(msg, f'{_safe_repr(s)} is not a string'))
        self.fail(self._formatMessage(msg, f"{_safe_repr(s)} doesn't start with {_safe_repr(prefix)}"))

    def assertNotStartsWith(self, s, prefix, msg=None):
        try:
            if not s.startswith(prefix):
                return
        except (AttributeError, TypeError):
            self.fail(self._formatMessage(msg, f'{_safe_repr(s)} is not a string'))
        self.fail(self._formatMessage(msg, f'{_safe_repr(s)} starts with {_safe_repr(prefix)}'))

    def assertEndsWith(self, s, suffix, msg=None):
        try:
            if s.endswith(suffix):
                return
        except (AttributeError, TypeError):
            self.fail(self._formatMessage(msg, f'{_safe_repr(s)} is not a string'))
        self.fail(self._formatMessage(msg, f"{_safe_repr(s)} doesn't end with {_safe_repr(suffix)}"))

    def assertNotEndsWith(self, s, suffix, msg=None):
        try:
            if not s.endswith(suffix):
                return
        except (AttributeError, TypeError):
            self.fail(self._formatMessage(msg, f'{_safe_repr(s)} is not a string'))
        self.fail(self._formatMessage(msg, f'{_safe_repr(s)} ends with {_safe_repr(suffix)}'))

    def assertLess(self, a, b, msg=None):
        if not a < b:
            self.fail(self._formatMessage(msg, f'{_safe_repr(a)} not less than {_safe_repr(b)}'))

    def assertLessEqual(self, a, b, msg=None):
        if not a <= b:
            self.fail(self._formatMessage(msg, f'{_safe_repr(a)} not less than or equal to {_safe_repr(b)}'))

    def assertGreater(self, a, b, msg=None):
        if not a > b:
            self.fail(self._formatMessage(msg, f'{_safe_repr(a)} not greater than {_safe_repr(b)}'))

    def assertGreaterEqual(self, a, b, msg=None):
        if not a >= b:
            self.fail(self._formatMessage(msg, f'{_safe_repr(a)} not greater than or equal to {_safe_repr(b)}'))

    def assertRaises(self, expected_exception, *args, **kwargs):
        context = _AssertRaises(self, expected_exception, msg=kwargs.pop('msg', None) if not args else None)
        if not args:
            if kwargs:
                raise TypeError(f'{next(iter(kwargs))!r} is an invalid keyword argument for this function')
            return context
        with context:
            args[0](*args[1:], **kwargs)

    def assertRaisesRegex(self, expected_exception, expected_regex, *args, **kwargs):
        context = _AssertRaises(self, expected_exception, expected_regex,
                                msg=kwargs.pop('msg', None) if not args else None)
        if not args:
            if kwargs:
                raise TypeError(f'{next(iter(kwargs))!r} is an invalid keyword argument for this function')
            return context
        with context:
            args[0](*args[1:], **kwargs)

    def assertWarns(self, *args, **kwargs):
        raise NotImplementedError('warning assertions are not supported by the test framework')

    assertWarnsRegex = assertWarns
    assertLogs = assertNoLogs = assertWarns


class TestSuite:
    def __init__(self, tests=()):
        self._tests = list(tests)

    def addTest(self, test):
        self._tests.append(test)

    def addTests(self, tests):
        for test in tests:
            self.addTest(test)

    def __iter__(self):
        return iter(self._tests)


def main(*args, **kwargs):
    raise NotImplementedError('unittest.main() is not supported by the test framework')


def _class_setup(cls):
    # The runner calls this in place of cls.setUpClass(); skipped classes
    # are not set up, as in unittest.suite.TestSuite._handleClassSetUp.
    if getattr(cls, '__unittest_skip__', False):
        raise SkipTest(getattr(cls, '__unittest_skip_why__', ''))
    cls.setUpClass()


def _run_case(cls, name):
    case = cls(name)
    method = getattr(case, name)
    if getattr(cls, '__unittest_skip__', False) or getattr(method, '__unittest_skip__', False):
        raise SkipTest(getattr(cls, '__unittest_skip_why__', '') or getattr(method, '__unittest_skip_why__', ''))
    expecting_failure = (getattr(method, '__unittest_expecting_failure__', False) or
                         getattr(case, '__unittest_expecting_failure__', False))
    try:
        case.setUp()
        try:
            try:
                method()
                if case._subtest_failures:
                    raise AssertionError(f'{case._subtest_failures} subtests failed')
            except SkipTest:
                raise
            except Exception:
                if not expecting_failure:
                    raise
            else:
                if expecting_failure:
                    raise AssertionError('unexpected success')
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
