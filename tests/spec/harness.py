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


def assert_raises(exception, function, *args, message=None, **kwargs):
    """Call function and require it to raise exception (a type or tuple).

    With message, str() of the exception must equal it. Returns the exception."""
    try:
        function(*args, **kwargs)
    except exception as caught:
        if message is not None and str(caught) != message:
            fail(f"{type(caught).__name__} message {str(caught)!r} != {message!r}")
        return caught
    except BaseException as other:
        fail(f"expected {exception!r}, got {type(other).__name__}: {other}")
    fail(f"expected {exception!r}, nothing was raised")


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
