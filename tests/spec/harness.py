"""Assertions for the language specification tests (tests/spec).

Each test is a standalone script that imports only this module. It passes by
running to completion; a failed check raises AssertionError naming it.
"""


class SpecFailure(AssertionError):
    pass


def fail(message):
    raise SpecFailure(message)


def assert_true(value, message="expected a true value"):
    if not value:
        fail(f"{message}: {value!r}")


def assert_false(value, message="expected a false value"):
    if value:
        fail(f"{message}: {value!r}")


def assert_eq(actual, expected, message=""):
    if not (actual == expected):
        fail(f"{message + ': ' if message else ''}{actual!r} != {expected!r}")


def assert_ne(actual, expected, message=""):
    if actual == expected:
        fail(f"{message + ': ' if message else ''}{actual!r} == {expected!r}")


def assert_is(actual, expected, message=""):
    if actual is not expected:
        fail(f"{message + ': ' if message else ''}{actual!r} is not {expected!r}")


def assert_type(value, expected, message=""):
    """value has exactly type expected (and compares equal when given a value)."""
    if type(value) is not expected:
        fail(f"{message + ': ' if message else ''}type {type(value).__name__} is not {expected.__name__}")


def assert_same(actual, expected, message=""):
    """Equal and of the same type: 1 and 1.0 and True are told apart."""
    if type(actual) is not type(expected) or not (actual == expected):
        fail(f"{message + ': ' if message else ''}{actual!r} ({type(actual).__name__}) is not "
             f"{expected!r} ({type(expected).__name__})")


class Raises:
    """The with-statement form of assert_raises; .exception holds what was caught."""

    def __init__(self, exception, message):
        self.expected, self.message, self.exception = exception, message, None

    def __enter__(self):
        return self

    def __exit__(self, kind, value, traceback):
        if kind is None:
            fail(f"expected {self.expected!r}, nothing was raised")
        if not issubclass(kind, self.expected):
            fail(f"expected {self.expected!r}, got {kind.__name__}: {value}")
        if self.message is not None and str(value) != self.message:
            fail(f"{kind.__name__} message {str(value)!r} != {self.message!r}")
        self.exception = value
        return True


def assert_raises(exception, function=None, *args, message=None, **kwargs):
    """Call function and require it to raise exception (a type or tuple).

    With message, str() of the exception must equal it. Returns the exception.
    Without function, return a context manager that checks its block."""
    if function is None:
        return Raises(exception, message)
    try:
        function(*args, **kwargs)
    except exception as caught:
        if message is not None and str(caught) != message:
            fail(f"{type(caught).__name__} message {str(caught)!r} != {message!r}")
        return caught
    except BaseException as other:
        fail(f"expected {exception!r}, got {type(other).__name__}: {other}")
    fail(f"expected {exception!r}, nothing was raised")


class TestFailingBool:
    """An object whose truth test raises RuntimeError."""

    def __bool__(self):
        raise RuntimeError


class TestFailingIter:
    """An iterable whose iter() raises RuntimeError."""

    def __iter__(self):
        raise RuntimeError


def assert_syntax_error(source, mode="exec", exception=SyntaxError):
    """compile(source) must raise SyntaxError (or the given subclass)."""
    try:
        compile(source, "<spec>", mode)
    except exception as caught:
        return caught
    except BaseException as other:
        fail(f"compiling {source!r}: expected {exception.__name__}, got {type(other).__name__}: {other}")
    fail(f"compiling {source!r}: expected {exception.__name__}, it compiled")


def assert_compiles(source, mode="exec"):
    try:
        return compile(source, "<spec>", mode)
    except SyntaxError as caught:
        fail(f"compiling {source!r} raised SyntaxError: {caught}")


def run(source, namespace=None):
    """Execute source in a fresh (or the given) namespace and return it."""
    namespace = {} if namespace is None else namespace
    exec(compile(source, "<spec>", "exec"), namespace)
    return namespace


# Host facilities (PLS-315 Annex B and C), like test262's $262. The Standard
# names no module through which a program reaches the module cache, the lazy
# module set, or the display hook, so a test reaches them only through this
# object. An implementation adapts this class to wherever its host exposes
# them; the definitions below use CPython's names (Annex C.5).
def run_program(source, stdin=""):
    """Run source as a main program whose print and input are bound in its
    namespace, and return what it printed, followed by the last line of a
    traceback when an exception escapes ("Type: message", 18.1.4)."""
    output = []
    lines = stdin.splitlines(keepends=True)

    def print_(*values, sep=" ", end="\n", file=None, flush=False):
        if sep is None:
            sep = " "
        if end is None:
            end = "\n"
        text = sep.join(str(value) for value in values) + end
        if file is None:
            output.append(text)
        else:
            file.write(text)

    def input_(prompt=""):
        output.append(str(prompt))
        if not lines:
            raise EOFError("EOF when reading a line")
        return lines.pop(0).rstrip("\n")

    # The program gets its own copy of the built-in namespace, so a program
    # that rebinds a built-in name (9.3) leaves the next one unaffected.
    builtins = __builtins__ if isinstance(__builtins__, dict) else vars(__builtins__)
    namespace = {"__name__": "__main__", "__builtins__": dict(builtins), "print": print_, "input": input_}
    try:
        exec(compile(source, "<program>", "exec"), namespace)
    except SystemExit as exit:
        if exit.code not in (None, 0):
            output.append(f"SystemExit: {exit.code}\n")
    except BaseException as error:
        message = str(error)
        output.append(f"{qualified(type(error))}: {message}\n" if message else f"{qualified(type(error))}\n")
    return "".join(output)


def check_program(source, expected, stdin=""):
    """The program's output (run_program) must be expected."""
    actual = run_program(source, stdin)
    if actual != expected:
        fail(f"program output differs:\n--- program\n{source}\n--- expected\n{expected}--- actual\n{actual}")


class Host:
    # The text by which messages name each facility: *host*(f) in 5.2.6.
    names = {
        "the module cache": "sys.modules",
        "standard input": "sys.stdin",
        "the int string limit": "sys.set_int_max_str_digits()",
    }

    def _sys(self):
        return __import__("sys")

    def name(self, facility):
        return self.names[facility]

    def module_cache(self):
        """The %ModuleCache% dict (17.3)."""
        return self._sys().modules

    def lazy_modules(self):
        """The %LazyModules% set of pending lazy submodule names (17.5)."""
        return self._sys().lazy_modules

    def display_hook(self):
        """The function HostDisplay calls for interactive expression statements."""
        return self._sys().displayhook

    def set_display_hook(self, hook):
        self._sys().displayhook = hook

    def collect(self):
        """Reclaim every unreachable object now, finalizers included (9.7)."""
        __import__("gc").collect()

    def warnings(self, thunk):
        """Call thunk and return the (category, message, line) of each
        warning HostWarn received meanwhile (18.3), shown, not raised; or
        None, after calling thunk, when the host supplies no HostWarn."""
        try:
            module = __import__("warnings")
        except ImportError:
            thunk()
            return None
        with module.catch_warnings(record=True) as caught:
            module.simplefilter("always")
            thunk()
        return [(w.category, str(w.message), w.lineno) for w in caught]

    def record_warnings(self):
        """Start recording the warnings HostWarn receives (18.3), shown, not
        raised. Return a function that stops and returns their (category,
        message, line) triples, or None when the host supplies no HostWarn."""
        try:
            module = __import__("warnings")
        except ImportError:
            return None
        catcher = module.catch_warnings(record=True)
        caught = catcher.__enter__()
        module.simplefilter("always")

        def stop():
            catcher.__exit__(None, None, None)
            return [(w.category, str(w.message), w.lineno) for w in caught]
        return stop

    def has_warnings(self):
        """Whether the host supplies HostWarn (18.3)."""
        try:
            __import__("warnings")
        except ImportError:
            return False
        return True

    def raising_warnings(self, thunk):
        """Call thunk with HostWarn raising every warning it receives as an
        exception (18.3), and return True; or return False without calling
        thunk when the host supplies no HostWarn."""
        try:
            module = __import__("warnings")
        except ImportError:
            return False
        with module.catch_warnings():
            module.simplefilter("error")
            thunk()
        return True

    def async_gen_hooks(self):
        """The (firstiter, finalizer) pair HostAsyncGenHooks returns (B.5.1),
        or None when the host offers programs no way to install them."""
        get = getattr(self._sys(), "get_asyncgen_hooks", None)
        return tuple(get()) if get else None

    def set_async_gen_hooks(self, firstiter, finalizer):
        self._sys().set_asyncgen_hooks(firstiter, finalizer)

    def recursion_limit(self):
        """The recursion limit execution parameter (B.6)."""
        return self._sys().getrecursionlimit()

    def set_recursion_limit(self, limit):
        self._sys().setrecursionlimit(limit)


host = Host()


def qualified(cls):
    """*tname* of an intrinsic type (PLS-315 5.2.6): its home module name,
    a dot, and its name, or the bare name for a type in builtins."""
    module = cls.__module__
    return cls.__name__ if module == "builtins" else f"{module}.{cls.__name__}"


def fqname(cls):
    """*fqname* (PLS-315 5.2.6): the qualified name, prefixed by the module
    unless that is builtins or __main__ (or not a str)."""
    module = cls.__module__
    if not isinstance(module, str) or module in ("builtins", "__main__"):
        return cls.__qualname__
    return f"{module}.{cls.__qualname__}"


# Doctests: CPython's interactive examples, run without the doctest module.
# Each example is compiled as interactive input; an expression's value is
# displayed with repr(), print() output is captured through the example
# globals, and an exception is compared by its last formatted line. The
# option directives behave as doctest's: ELLIPSIS, NORMALIZE_WHITESPACE,
# IGNORE_EXCEPTION_DETAIL, DONT_ACCEPT_BLANKLINE, DONT_ACCEPT_TRUE_FOR_1, SKIP.

def _doctest_examples(text):
    """Parse docstring text into (line, source, want, exc_msg, options)."""
    lines = text.split("\n")
    examples, i = [], 0
    while i < len(lines):
        stripped = lines[i].lstrip(" ")
        if not (stripped.startswith(">>> ") or stripped == ">>>"):
            i += 1
            continue
        indent, start = len(lines[i]) - len(stripped), i
        source = [stripped[4:]]
        i += 1
        while i < len(lines) and lines[i][indent:].startswith("...") and lines[i][indent:indent + 4] in ("... ", "..."):
            source.append(lines[i][indent + 4:])
            i += 1
        want = []
        while i < len(lines) and lines[i].strip() and not lines[i].lstrip(" ").startswith(">>>"):
            want.append(lines[i][indent:])
            i += 1
        options = {}
        for line in source:
            at = line.find("#")
            while at >= 0:
                rest = line[at + 1:].lstrip()
                if rest.startswith("doctest:"):
                    for item in rest[len("doctest:"):].replace(",", " ").split():
                        options[item[1:]] = item[0] == "+"
                at = line.find("#", at + 1)
        source = "\n".join(source)
        if not source.endswith("\n"):
            source += "\n"
        want = "\n".join(want) + "\n" if want else ""
        exc_msg = None
        if want.startswith(("Traceback (most recent call last):", "Traceback (innermost last):")):
            rest = want.split("\n")[1:]
            for k, line in enumerate(rest):
                if line[:1].isalnum() or line[:1] == "_":
                    exc_msg = "\n".join(rest[k:])
                    break
        # doctest ignores examples that are only blank lines or comments.
        if any(line.strip() and not line.strip().startswith("#") for line in source.split("\n")):
            examples.append((start, source, want, exc_msg, options))
    return examples


def _ellipsis_match(want, got):
    pieces = want.split("...")
    if len(pieces) == 1:
        return want == got
    start, end = pieces[0], pieces[-1]
    if not got.startswith(start) or not got.endswith(end) or len(start) + len(end) > len(got):
        return False
    position, limit = len(start), len(got) - len(end)
    for piece in pieces[1:-1]:
        found = got.find(piece, position, limit)
        if found < 0:
            return False
        position = found + len(piece)
    return True


def _blank_lines(text, marker):
    lines = text.split("\n")
    if marker:
        return "\n".join("" if line.rstrip() == "<BLANKLINE>" else line for line in lines)
    return "\n".join("" if not line.strip() else line for line in lines)


def _doctest_check(want, got, options):
    if got == want:
        return True
    if not options.get("DONT_ACCEPT_TRUE_FOR_1"):
        if (got, want) in (("True\n", "1\n"), ("False\n", "0\n")):
            return True
    if not options.get("DONT_ACCEPT_BLANKLINE"):
        want, got = _blank_lines(want, True), _blank_lines(got, False)
        if got == want:
            return True
    if options.get("NORMALIZE_WHITESPACE"):
        got, want = " ".join(got.split()), " ".join(want.split())
        if got == want:
            return True
    return bool(options.get("ELLIPSIS")) and _ellipsis_match(want, got)


def _exception_line(error):
    """The last line traceback.format_exception_only would produce."""
    kind = type(error)
    name = kind.__qualname__
    if kind.__module__ not in ("__main__", "builtins"):
        name = kind.__module__ + "." + name
    notes = getattr(error, "__notes__", None)
    if isinstance(notes, (list, tuple)) and notes:
        return str(notes[-1]) + "\n"
    if isinstance(error, SyntaxError):
        return f"{name}: {error.msg or '<no detail available>'}\n"
    try:
        message = str(error)
    except BaseException:
        message = "<exception str() failed>"
    return f"{name}: {message}\n" if message else name + "\n"


def _detail_free(message):
    """IGNORE_EXCEPTION_DETAIL: the exception class name without its module."""
    head = message.split(":", 1)[0] + ":" if ":" in message else message.rstrip("\n")
    return head.rsplit(".", 1)[-1]


def run_doctests(name, text, setup="", globs=None):
    """Run the examples in text as one doctest group of module name.

    setup is source executed first in the group's globals: the module-level
    definitions its examples rely on."""
    output = []
    def capture(*args, sep=" ", end="\n", file=None, flush=False):
        if file is not None:
            return print(*args, sep=sep, end=end, file=file, flush=flush)
        if sep is not None and not isinstance(sep, str):
            raise TypeError(f"sep must be None or a string, not {type(sep).__name__}")
        if end is not None and not isinstance(end, str):
            raise TypeError(f"end must be None or a string, not {type(end).__name__}")
        output.append((" " if sep is None else sep).join(str(arg) for arg in args) + ("\n" if end is None else end))
    namespace = dict(globs or {})
    namespace["__name__"] = name
    namespace["print"] = capture
    if setup:
        exec(compile(setup, f"<doctest {name} setup>", "exec"), namespace)
    failures, examples = [], _doctest_examples(text)
    for index, (line, source, want, exc_msg, options) in enumerate(examples):
        if options.get("SKIP"):
            continue
        output.clear()
        filename = f"<doctest {name}[{index}]>"
        error = None
        try:
            compile(source, filename, "single")
            try:
                code = compile(source, filename, "eval")
            except SyntaxError:
                code = None
            if code is not None:
                value = eval(code, namespace)
                if value is not None:
                    output.append(repr(value) + "\n")
            else:
                exec(compile(source, filename, "exec"), namespace)
        except KeyboardInterrupt:
            raise
        except BaseException as caught:
            error = caught
        got = "".join(output)
        if got and not got.endswith("\n"):
            got += "\n"
        if error is None:
            passed = exc_msg is None and _doctest_check(want, got, options)
            if exc_msg is not None:
                got += "(no exception raised)\n"
        else:
            actual = _exception_line(error)
            passed = exc_msg is not None and _doctest_check(exc_msg, actual, options)
            if not passed and exc_msg is not None and options.get("IGNORE_EXCEPTION_DETAIL"):
                passed = _detail_free(exc_msg) == _detail_free(actual)
            got = "Traceback (most recent call last):\n" + actual
            error = None
        if not passed:
            failures.append(f"line {line + 1}: {source.rstrip()}\n  expected: {want!r}\n  got:      {got!r}")
    if failures:
        fail(f"{len(failures)} of {len(examples)} examples in {name} failed:\n" + "\n".join(failures))
    return len(examples)


# Ported unittest modules
#
# A core-only adaptation of unittest for CPython test modules ported to
# tests/spec/ports: the TestCase assertions, skips, subtests, fixtures, and a
# backtracking subset of re.search for assertRaisesRegex and assertRegex.

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


class _AssertWarns:
    def __init__(self, testcase, category, regex):
        self.testcase, self.category, self.regex = testcase, category, regex
        self.warning = self.filename = self.lineno = None

    def __enter__(self):
        self.stop = host.record_warnings()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if self.stop is None:
            return False
        caught = self.stop()
        if exc_type is not None:
            return False
        categories = self.category if isinstance(self.category, tuple) else (self.category,)
        for category, message, line in caught:
            if issubclass(category, categories) and (self.regex is None or _search(self.regex, message)):
                self.warning, self.lineno = category(message), line
                return False
        names = ", ".join(c.__name__ for c in categories)
        self.testcase.fail(f"{names} not triggered" + (f" matching {self.regex!r}" if self.regex else ""))


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
        # As CPython: equal items in equal numbers make different sequence types equal.
        for i in range(min(len(seq1), len(seq2))):
            try:
                item1, item2 = seq1[i], seq2[i]
            except (TypeError, IndexError, NotImplementedError):
                break
            if item1 != item2:
                break
        else:
            if len(seq1) == len(seq2) and seq_type is None and type(seq1) != type(seq2):
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

    def assertWarns(self, expected_warning, *args, **kwargs):
        """A warning of the category is required only where the host
        supplies HostWarn (18.3); otherwise the code just runs."""
        context = _AssertWarns(self, expected_warning, None)
        if not args:
            return context
        with context:
            args[0](*args[1:], **kwargs)

    def assertWarnsRegex(self, expected_warning, expected_regex, *args, **kwargs):
        context = _AssertWarns(self, expected_warning, expected_regex)
        if not args:
            return context
        with context:
            args[0](*args[1:], **kwargs)

    def assertLogs(self, *args, **kwargs):
        raise NotImplementedError('log assertions are not supported by the test framework')

    assertNoLogs = assertLogs


def _test_names(cls):
    return sorted(name for name in dir(cls) if name.startswith("test") and callable(getattr(cls, name)))


def _run_case(cls, name):
    case = cls(name)
    method = getattr(case, name)
    if getattr(cls, "__unittest_skip__", False) or getattr(method, "__unittest_skip__", False):
        raise SkipTest(getattr(cls, "__unittest_skip_why__", "") or getattr(method, "__unittest_skip_why__", ""))
    expecting_failure = (getattr(method, "__unittest_expecting_failure__", False) or
                         getattr(case, "__unittest_expecting_failure__", False))
    try:
        case.setUp()
        try:
            try:
                method()
                if case._subtest_failures:
                    failed = [entry for entry in case._subtests if entry[2] == "failed"]
                    raise AssertionError(f"{case._subtest_failures} subtests failed: {failed}")
            except SkipTest:
                raise
            except Exception:
                if not expecting_failure:
                    raise
            else:
                if expecting_failure:
                    raise AssertionError("unexpected success")
        finally:
            case.tearDown()
    finally:
        case.doCleanups()


def run_tests(namespace):
    """Run every TestCase subclass defined in namespace, as unittest.main()
    would: classes and their test* methods in name order, with class and
    method fixtures. Fail listing the tests that failed."""
    module = namespace.get("__name__")
    classes = sorted((value for value in namespace.values()
                      if isinstance(value, type) and issubclass(value, TestCase) and value is not TestCase
                      and value.__module__ == module and _test_names(value)), key=lambda cls: cls.__name__)
    failures, ran = [], 0
    for cls in classes:
        if getattr(cls, "__unittest_skip__", False):
            continue
        try:
            cls.setUpClass()
        except SkipTest:
            continue
        except Exception as error:
            failures.append(f"{cls.__name__}.setUpClass: {type(error).__name__}: {error}")
            continue
        try:
            for name in _test_names(cls):
                try:
                    _run_case(cls, name)
                    ran += 1
                except SkipTest:
                    pass
                except Exception as error:
                    failures.append(f"{cls.__name__}.{name}: {type(error).__name__}: {error}")
        finally:
            cls.tearDownClass()
            cls.doClassCleanups()
    if failures:
        fail(f"{len(failures)} tests failed:\n" + "\n".join(failures))
    if not ran:
        fail("no test ran")
    return ran


class unittest:
    """The unittest names ported upstream modules use (tests/spec/ports)."""
    TestCase = TestCase
    SkipTest = SkipTest
    skip = staticmethod(skip)
    skipIf = staticmethod(skipIf)
    skipUnless = staticmethod(skipUnless)
    expectedFailure = staticmethod(expectedFailure)

    @staticmethod
    def main(*args, **kwargs):
        """Run the tests of the calling module, found through its frame."""
        try:
            raise SkipTest
        except SkipTest as caught:
            namespace = caught.__traceback__.tb_frame.f_back.f_globals
        return run_tests(namespace)


class operator:
    """Core equivalents of the operator functions ported modules use."""
    lt = __lt__ = staticmethod(lambda a, b: a < b)
    le = __le__ = staticmethod(lambda a, b: a <= b)
    eq = __eq__ = staticmethod(lambda a, b: a == b)
    ne = __ne__ = staticmethod(lambda a, b: a != b)
    gt = __gt__ = staticmethod(lambda a, b: a > b)
    ge = __ge__ = staticmethod(lambda a, b: a >= b)
    not_ = __not__ = staticmethod(lambda a: not a)
    truth = staticmethod(lambda a: bool(a))
    is_ = staticmethod(lambda a, b: a is b)
    is_not = staticmethod(lambda a, b: a is not b)
    contains = __contains__ = staticmethod(lambda a, b: b in a)
    getitem = __getitem__ = staticmethod(lambda a, b: a[b])
    neg = __neg__ = staticmethod(lambda a: -a)
    add = __add__ = staticmethod(lambda a, b: a + b)
    sub = __sub__ = staticmethod(lambda a, b: a - b)
    mul = __mul__ = staticmethod(lambda a, b: a * b)
    mod = __mod__ = staticmethod(lambda a, b: a % b)
    pow = __pow__ = staticmethod(lambda a, b: a ** b)

    @staticmethod
    def index(a):
        """ToIndex (7.5.3), which a range applies to its bound."""
        return range(a).stop

    @staticmethod
    def length_hint(obj, default=0):
        """len(obj), else type(obj).__length_hint__(obj), else default."""
        try:
            return len(obj)
        except TypeError:
            pass
        hint = getattr(type(obj), "__length_hint__", None)
        if hint is None:
            return default
        value = hint(obj)
        if value is NotImplemented:
            return default
        if not isinstance(value, int):
            raise TypeError("__length_hint__ must be an integer, not %s" % type(value).__name__)
        if value < 0:
            raise ValueError("__length_hint__() should return >= 0")
        return value

    @staticmethod
    def setitem(a, b, c):
        a[b] = c

    @staticmethod
    def delitem(a, b):
        del a[b]

    @staticmethod
    def countOf(a, b):
        """The number of items of a that are b or equal to it."""
        count = 0
        for item in a:
            if item is b or item == b:
                count += 1
        return count

    @staticmethod
    def indexOf(a, b):
        """The index of the first item of a that is b or equal to it."""
        for i, item in enumerate(a):
            if item is b or item == b:
                return i
        raise ValueError("sequence.index(x): x not in sequence")


class pickle:
    """A stand-in for the pickle module over the core reduction protocol
    (20.1.4): dumps() snapshots an object as its reduction tree, taking
    __reduce_ex__(protocol) of every object other than a scalar, tuple,
    list, dict, set or bytearray, and loads() rebuilds fresh objects from
    the snapshot by calling the reductions and applying their state.
    Functions and classes are kept by reference."""
    HIGHEST_PROTOCOL = DEFAULT_PROTOCOL = 5

    class PicklingError(Exception):
        pass

    class _Pickled:
        def __init__(self, tree):
            self.tree = tree

    _SCALARS = (type(None), bool, int, float, complex, str, bytes, type(Ellipsis), type(NotImplemented))
    _REFERENCES = (type, type(len), type(lambda: 0), type([].append))

    @classmethod
    def dumps(cls, obj, protocol=None):
        return cls._Pickled(cls._freeze(obj, cls.DEFAULT_PROTOCOL if protocol is None else protocol, {}))

    @classmethod
    def loads(cls, data):
        return cls._thaw(data.tree, {})

    @classmethod
    def _freeze(cls, obj, protocol, memo):
        kind = type(obj)
        if kind in cls._SCALARS or isinstance(obj, cls._REFERENCES):
            if isinstance(obj, type(lambda: 0)) and obj.__name__ == "<lambda>":
                raise cls.PicklingError("Can't pickle %r: it's not found as __main__.<lambda>" % (obj,))
            return ("atom", obj)
        key = id(obj)
        if key in memo:
            return ("ref", key)
        memo[key] = obj
        freeze = lambda value: cls._freeze(value, protocol, memo)
        if kind is tuple:
            return ("tuple", key, [freeze(item) for item in obj])
        if kind is list:
            return ("list", key, [freeze(item) for item in obj])
        if kind is dict:
            return ("dict", key, [(freeze(k), freeze(v)) for k, v in obj.items()])
        if kind in (set, frozenset):
            return ("set", key, kind, [freeze(item) for item in obj])
        if kind is bytearray:
            return ("bytearray", key, bytes(obj))
        reduced = obj.__reduce_ex__(protocol)
        if isinstance(reduced, str):
            return ("atom", obj)
        reduced = tuple(reduced) + (None,) * (5 - len(reduced))
        func, args, state, listitems, dictitems = reduced
        return ("reduce", key, freeze(func), freeze(args), freeze(state),
                None if listitems is None else [freeze(item) for item in listitems],
                None if dictitems is None else [(freeze(k), freeze(v)) for k, v in dictitems])

    @classmethod
    def _thaw(cls, tree, memo):
        kind = tree[0]
        if kind == "atom":
            return tree[1]
        if kind == "ref":
            return memo[tree[1]]
        thaw = lambda node: cls._thaw(node, memo)
        key = tree[1]
        if kind == "tuple":
            memo[key] = result = tuple(thaw(item) for item in tree[2])
        elif kind == "list":
            memo[key] = result = []
            result.extend(thaw(item) for item in tree[2])
        elif kind == "dict":
            memo[key] = result = {}
            for k, v in tree[2]:
                result[thaw(k)] = thaw(v)
        elif kind == "set":
            memo[key] = result = tree[2](thaw(item) for item in tree[3])
        elif kind == "bytearray":
            memo[key] = result = bytearray(tree[2])
        else:
            func, args = thaw(tree[2]), thaw(tree[3])
            memo[key] = result = func(*args)
            state = thaw(tree[4])
            if state is not None:
                setstate = getattr(result, "__setstate__", None)
                if setstate is not None:
                    setstate(state)
                else:
                    slots = None
                    if isinstance(state, tuple) and len(state) == 2:
                        state, slots = state
                    if state:
                        result.__dict__.update(state)
                    for name, value in (slots or {}).items():
                        setattr(result, name, value)
            for item in tree[5] or ():
                result.append(thaw(item))
            for k, v in tree[6] or ():
                result[thaw(k)] = thaw(v)
        return result


class random:
    """A fixed pseudo-random sequence (a linear congruential generator) for
    the random module functions ported modules use; tests need only
    varied, reproducible values."""
    _state = 12345

    @classmethod
    def seed(cls, value=12345):
        cls._state = hash(value) % 2 ** 31

    @classmethod
    def _bits(cls):
        cls._state = (cls._state * 1103515245 + 12345) % 2 ** 31
        return cls._state

    @classmethod
    def randrange(cls, start, stop=None, step=1):
        if stop is None:
            start, stop = 0, start
        width = (stop - start + step - 1) // step
        if width <= 0:
            raise ValueError(f"empty range in randrange({start}, {stop})")
        value, scale = 0, 1
        while scale < width * 2 ** 31:
            value = value * 2 ** 31 + cls._bits()
            scale *= 2 ** 31
        return start + step * (value % width)

    @classmethod
    def randint(cls, a, b):
        return cls.randrange(a, b + 1)

    @classmethod
    def random(cls):
        return cls._bits() / 2 ** 31

    @classmethod
    def choice(cls, seq):
        return seq[cls.randrange(len(seq))]

    @classmethod
    def shuffle(cls, items):
        for i in range(len(items) - 1, 0, -1):
            j = cls.randrange(i + 1)
            items[i], items[j] = items[j], items[i]


class _NeverEq:
    def __eq__(self, other):
        return False
    def __ne__(self, other):
        return True
    def __hash__(self):
        return 1


class _AlwaysEq:
    def __eq__(self, other):
        return True
    def __ne__(self, other):
        return False


class _Largest:
    def __eq__(self, other):
        return isinstance(other, _Largest)
    def __lt__(self, other):
        return False
    def __le__(self, other):
        return self == other
    def __gt__(self, other):
        return not self == other
    def __ge__(self, other):
        return True


class _Smallest:
    def __eq__(self, other):
        return isinstance(other, _Smallest)
    def __gt__(self, other):
        return False
    def __ge__(self, other):
        return self == other
    def __lt__(self, other):
        return not self == other
    def __le__(self, other):
        return True


class _BrokenIter:
    def __init__(self, init_raises=False, next_raises=False, iter_raises=False):
        if init_raises:
            1/0
        self.next_raises = next_raises
        self.iter_raises = iter_raises

    def __next__(self):
        if self.next_raises:
            1/0

    def __iter__(self):
        if self.iter_raises:
            1/0
        return self


class support:
    """Core equivalents of the test.support helpers ported modules use."""
    BrokenIter = _BrokenIter
    MAX_Py_ssize_t = 2 ** 63 - 1  # the index-size range of Annex D
    NEVER_EQ = _NeverEq()
    ALWAYS_EQ = _AlwaysEq()
    LARGEST = _Largest()
    SMALLEST = _Smallest()

    @staticmethod
    def check_syntax_error(testcase, statement, errtext="", *, lineno=None, offset=None):
        with testcase.assertRaisesRegex(SyntaxError, errtext) as cm:
            compile(statement, "<test string>", "exec")
        err = cm.exception
        testcase.assertIsNotNone(err.lineno)
        if lineno is not None:
            testcase.assertEqual(err.lineno, lineno)
        testcase.assertIsNotNone(err.offset)
        if offset is not None:
            testcase.assertEqual(err.offset, offset)

    @staticmethod
    def gc_collect():
        host.collect()

    @staticmethod
    def check_free_after_iterating(test, iter, cls, args=()):
        """The iterable is released once its iterator is exhausted, and
        then calling next() on it from __del__ raises StopIteration."""
        done = False
        def wrapper():
            class A(cls):
                def __del__(self):
                    nonlocal done
                    try:
                        next(it)
                    except StopIteration:
                        done = True
            it = iter(A(*args))
            test.assertRaises(StopIteration, next, it)
        wrapper()
        support.gc_collect()
        test.assertTrue(done)

    @staticmethod
    def refcount_test(test):
        """Reference counts are an implementation detail outside PLS-315."""
        return skip("reference counts are an implementation detail")(test)

    @staticmethod
    def requires_docstrings(test):
        """Docstrings are kept at the default optimization level (Annex D)."""
        return test

    @staticmethod
    def no_tracing(test):
        """Tracing is a host facility outside PLS-315."""
        return test

    @staticmethod
    def cpython_only(test):
        """CPython implementation details are outside PLS-315."""
        return skip("CPython implementation detail")(test)

    @staticmethod
    def exceeds_recursion_limit():
        """A depth well past any recursion limit (9.6)."""
        return 150_000

    @staticmethod
    def skip_if_huge_c_stack(*args, **kwargs):
        return lambda test: test

    skip_emscripten_stack_overflow = skip_wasi_stack_overflow = skip_if_huge_c_stack

    @staticmethod
    def thread_unsafe(reason=None):
        """Free-threaded test runs are a host facility outside PLS-315."""
        return lambda test: test

    @staticmethod
    def infinite_recursion(max_depth=None):
        """Lower the recursion limit to max_depth frames past the depth at
        which the block is entered (counted through frame objects, 28.3)
        while it runs; also usable as a decorator."""
        if max_depth is None:
            max_depth = 20_000
        elif max_depth < 3:
            raise ValueError(f"max_depth must be at least 3, got {max_depth}")
        return _RecursionLimit(max_depth)


class _RecursionLimit:
    def __init__(self, max_depth):
        self.max_depth = max_depth

    def __enter__(self):
        try:
            raise SkipTest
        except SkipTest as caught:
            frame = caught.__traceback__.tb_frame.f_back
        depth = 0
        while frame is not None:
            depth += 1
            frame = frame.f_back
        self.saved = host.recursion_limit()
        host.set_recursion_limit(max(depth - 1, 1) + self.max_depth)

    def __exit__(self, *exc):
        host.set_recursion_limit(self.saved)

    def __call__(self, function):
        def wrapper(*args, **kwargs):
            with self:
                return function(*args, **kwargs)
        wrapper.__name__ = function.__name__
        return wrapper
