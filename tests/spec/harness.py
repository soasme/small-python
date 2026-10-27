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
