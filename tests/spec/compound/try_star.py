# spec: PLS-315 15.4.3
# description: except* matching through split, the handled exception, and re-raised tracebacks.
from harness import *

def variants(source, **names):
    """The function source defines, as written and as a generator's body,
    which runs suspendably. Each is called to completion; what it raises
    is returned."""
    def complete(function):
        def run():
            try:
                result = function()
                if type(result).__name__ == "generator": list(result)
            except BaseException as error:
                return error
        run.code = function.__code__
        return run
    out = []
    for text in (source, source + "    if False: yield\n"):
        namespace = dict(names)
        exec(text, namespace)
        out.append(complete(namespace["f"]))
    return out

def lines(error, code):
    """The traceback lines of error in code, relative to its first line."""
    out, tb = [], error.__traceback__
    while tb:
        if tb.tb_frame.f_code is code: out.append(tb.tb_lineno - code.co_firstlineno)
        tb = tb.tb_next
    return out

# A group that matches no clause type in full splits itself through its
# own split method, whose result must be a tuple of at least two items.
calls, matches = [], []
class Logged(ExceptionGroup):
    def split(self, condition):
        calls.append(condition)
        return super().split(condition) + ("ignored",)
for run in variants("""
def f():
    try:
        raise Logged("eg", [ValueError(1), TypeError(2)])
    except* ValueError as match:
        matches.append(repr(match))
    except* TypeError:
        pass
""", Logged=Logged, matches=matches):
    assert_is(run(), None)
    # The rest is an ExceptionGroup, which Logged.derive does not override.
    assert_eq(calls, [ValueError])
    assert_eq(matches, ["ExceptionGroup('eg', [ValueError(1)])"])
    calls.clear(); matches.clear()

class NotTuple(ExceptionGroup):
    def split(self, condition):
        return [None, None]
class Short(ExceptionGroup):
    def split(self, condition):
        return (None,)
for cls, message in ((NotTuple, "NotTuple.split must return a tuple, not list"),
                     (Short, "Short.split must return a 2-tuple, got tuple of size 1")):
    for run in variants("""
def f():
    try:
        raise cls("eg", [ValueError(1)])
    except* ValueError:
        pass
""", cls=cls):
        error = run()
        assert_type(error, TypeError)
        assert_eq(str(error), message)
        # The group is the handled exception while the clause matches.
        assert_type(error.__context__, cls)

# A full match takes the whole group without splitting it.
for run in variants("""
def f():
    try:
        raise Logged("eg", [ValueError(1)])
    except* Exception as match:
        matches.append(type(match).__name__)
""", Logged=Logged, matches=matches):
    run()
    assert_eq((calls, matches), ([], ["Logged"]))
    matches.clear()

# The group is handled while the first clause matches; from then on, the
# last match, which is never reset to the group.
seen = []
def handled(label):
    seen.append((label, repr(host.exception())))
    return label
for run in variants("""
def f():
    try:
        raise ExceptionGroup("eg", [ValueError(1), TypeError(2), KeyError(3)])
    except* (handled("first") and ValueError):
        pass
    except* (handled("second") and TypeError):
        pass
    except* (handled("third") and OSError):
        pass
""", handled=handled):
    assert_eq(repr(run()), "ExceptionGroup('eg', [KeyError(3)])")
    assert_eq(seen, [("first", "ExceptionGroup('eg', [ValueError(1), TypeError(2), KeyError(3)])"),
                     ("second", "ExceptionGroup('eg', [ValueError(1)])"),
                     ("third", "ExceptionGroup('eg', [TypeError(2)])")])
    seen.clear()

# A naked exception that matches is wrapped in a group whose traceback
# starts at the clause.
for run in variants("""
def f():
    try:
        raise ValueError(1)
    except* ValueError as match:
        matches.append(match)
""", matches=matches):
    run()
    match, = matches
    assert_eq((lines(match, run.code), lines(match.exceptions[0], run.code)), ([3], [2]))
    matches.clear()

# Propagation re-raises: the running frame adds no traceback entry, for an
# unhandled rest, a re-raised match, or a new exception.
for source, outer, inner in (("""
def f():
    try:
        raise ExceptionGroup("eg", [ValueError(1), TypeError(2)])
    except* ValueError:
        pass
""", [2], [[]]), ("""
def f():
    try:
        raise ExceptionGroup("eg", [ValueError(1), TypeError(2)])
    except* ValueError:
        raise
""", [2], [[], []]), ("""
def f():
    try:
        raise ExceptionGroup("eg", [ValueError(1), TypeError(2)])
    except* ValueError:
        raise KeyError(3)
""", [], [[4], [2]]), ("""
def f():
    try:
        raise ValueError(1)
    except* ValueError:
        raise KeyError(3)
""", [4], None)):
    for run in variants(source):
        error = run()
        assert_eq(lines(error, run.code), outer)
        if inner is not None:
            assert_eq([lines(e, run.code) for e in error.exceptions], inner)

# A function that calls nothing runs except*, else and finally the same way.
group = ExceptionGroup("g", [ValueError(1)])
def star_raising():
    global star_final
    try:
        raise group
    except* ValueError:
        raise KeyError
    finally:
        star_final = 1
def star_else():
    global star_branch
    try:
        star_branch = 0
    except* ValueError:
        star_branch = 1
    else:
        star_branch = 2
try:
    star_raising()
except KeyError as e:
    assert type(e.__context__) is ExceptionGroup
star_else()
assert (star_final, star_branch) == (1, 2)

# A clause that matches nothing passes on what the split left, a new
# ExceptionGroup, so later clauses split that.
group = Logged("eg", [ValueError(1), TypeError(2)])
failure = KeyError(3)
def plain():
    try:
        raise group
    except* KeyError:
        caught = 0
    except* ValueError as match:
        caught = match
    except* TypeError:
        rest = 1
    finally:
        done = 1
    return caught, rest, done
def raising():
    try:
        raise group
    except* ValueError:
        1 / 0
def unhandled():
    try:
        raise group
    except* ValueError:
        caught = 1
    finally:
        done = 1
def overriding():
    try:
        raise group
    except* ValueError:
        caught = 1
    finally:
        raise failure
def outcome(f):
    try:
        return f()
    except BaseException as error:
        return error
def outcomes():
    out = []
    for f in (plain, raising, unhandled, overriding):
        out.append((repr(outcome(f)), [c.__name__ for c in calls]))
        calls.clear()
    return out
expected_outcomes = [("(ExceptionGroup('eg', [ValueError(1)]), 1, 1)", ['KeyError']), ("ExceptionGroup('', [ZeroDivisionError('division by zero'), ExceptionGroup('eg', [TypeError(2)])])", ['ValueError']), ("ExceptionGroup('eg', [TypeError(2)])", ['ValueError']), ('KeyError(3)', ['ValueError'])]
assert_eq(outcomes(), expected_outcomes)

# A naked exception raised with no call in the body matches the same way,
# a full match wrapped in a group.
def matched_plain():
    try:
        1 / 0
    except* KeyError:
        caught = 0
    except* ZeroDivisionError as match:
        caught = match
    finally:
        done = 1
    return caught, done
def raising_plain():
    try:
        1 / 0
    except* ZeroDivisionError:
        missing
def unhandled_plain():
    try:
        1 / 0
    except* KeyError:
        caught = 1
    finally:
        done = 1
def overriding_plain():
    try:
        1 / 0
    except* ZeroDivisionError:
        caught = 1
    finally:
        missing
def otherwise_plain():
    try:
        done = 0
    except* ValueError:
        done = 1
    else:
        done = 2
    return done
assert_eq([repr(outcome(f)) for f in (matched_plain, raising_plain, unhandled_plain, overriding_plain, otherwise_plain)],
          ["(ExceptionGroup('', (ZeroDivisionError('division by zero'),)), 1)", 'NameError("name \'missing\' is not defined")',
           "ZeroDivisionError('division by zero')", 'NameError("name \'missing\' is not defined")', '2'])
