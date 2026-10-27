# spec: reference/compound_stmts.html#the-if-statement
# description: if/elif/else, while and for with else, break/continue, try/except/else/finally, except*, and with statements.
from harness import *

# if evaluates conditions in order and runs only the first true branch.
log = []
def cond(name, value):
    log.append(name)
    return value
if cond("a", 0): pass
elif cond("b", ""): pass
elif cond("c", [1]): branch = "c"
elif cond("d", 1): branch = "d"
else: branch = "else"
assert_eq((branch, log), ("c", ["a", "b", "c"]))

# while: else runs when the condition becomes false, not after break.
n, seen = 0, []
while n < 3:
    n += 1
    if n == 2: continue
    seen.append(n)
else:
    seen.append("else")
assert_eq(seen, [1, 3, "else"])
n = 0
while True:
    n += 1
    if n == 5: break
else:
    fail("while-else ran after break")
assert_eq(n, 5)
while 0:
    fail("body of while 0")
else:
    ran = True
assert_true(ran)

# for assigns each item to the target list, with else when exhausted.
pairs = []
for i, (a, *rest) in enumerate([(1, 2, 3), (4,)]):
    pairs.append((i, a, rest))
else:
    pairs.append("done")
assert_eq(pairs, [(0, 1, [2, 3]), (1, 4, []), "done"])
for x in []:
    fail("empty loop body")
else:
    empty_else = True
assert_true(empty_else)
# The target keeps its last value; an empty iterable leaves it unbound.
for last in range(3): pass
assert_eq(last, 2)
def unbound():
    for never in (): pass
    return never
assert_raises(UnboundLocalError, unbound)
# Targets may be attributes and subscriptions, assigned in order.
class Box: pass
box, slots = Box(), [0, 0]
for box.value, slots[box.value] in [(0, "a"), (1, "b")]: pass
assert_eq((box.value, slots), (1, ["a", "b"]))
# Modifying the loop variable does not affect iteration.
out = []
for i in range(3):
    out.append(i)
    i = 10
assert_eq(out, [0, 1, 2])
# break and continue inside finally (allowed since 3.8, a SyntaxWarning in 3.14+).
# continue in a nested loop only affects the innermost loop.
grid = []
for i in range(3):
    for j in range(3):
        if j == 1: continue
        if j == 2: break
        grid.append((i, j))
assert_eq(grid, [(0, 0), (1, 0), (2, 0)])
assert_syntax_error("break\n")
assert_syntax_error("continue\n")
assert_syntax_error("def f():\n    break\n")
assert_syntax_error("for x in y:\n    def f():\n        continue\n")
assert_syntax_error("while 1:\n    class C:\n        break\n")

# try/except: the first matching handler runs; the name is unbound afterwards.
def classify(error):
    try:
        raise error
    except (KeyError, IndexError) as e:
        return "lookup", e.args
    except ArithmeticError:
        return "arith"
    except Exception:
        return "other"
assert_eq(classify(KeyError("k")), ("lookup", ("k",)))
assert_eq(classify(ZeroDivisionError), "arith")
assert_eq(classify(ValueError), "other")
def name_cleared():
    e = "before"
    try:
        1 / 0
    except ZeroDivisionError as e:
        pass
    return e
assert_raises(UnboundLocalError, name_cleared)
# except without parentheses for several types (PEP 758, 3.14).
try:
    raise IndexError
except KeyError, IndexError:
    multi = True
assert_true(multi)
assert_syntax_error("try:\n    pass\nexcept A, B as e:\n    pass\n")
# An expression that is not an exception class fails when matching.
def bad_handler():
    try:
        raise ValueError
    except 42:
        pass
e = assert_raises(TypeError, bad_handler)
assert_eq(str(e), "catching classes that do not inherit from BaseException is not allowed")
# A bare except must be last.
assert_syntax_error("try:\n    pass\nexcept:\n    pass\nexcept ValueError:\n    pass\n")
# try needs at least one except or finally.
assert_syntax_error("try:\n    pass\n")
assert_syntax_error("try:\n    pass\nelse:\n    pass\n")

# else runs when no exception occurred; finally always runs.
def flow(raise_it):
    events = []
    try:
        events.append("try")
        if raise_it: raise ValueError
    except ValueError:
        events.append("except")
    else:
        events.append("else")
    finally:
        events.append("finally")
    return events
assert_eq(flow(False), ["try", "else", "finally"])
assert_eq(flow(True), ["try", "except", "finally"])
# An exception from else is not caught by the same try's handlers.
def else_raises():
    try:
        pass
    except ValueError:
        return "caught"
    else:
        raise ValueError("from else")
assert_raises(ValueError, else_raises, message="from else")
# finally's return overrides the try's return and discards an exception.
def finally_return():
    try:
        return "try"
    finally:
        return "finally"
assert_eq(finally_return(), "finally")
def finally_swallows():
    try:
        raise KeyError
    finally:
        return "swallowed"
assert_eq(finally_swallows(), "swallowed")
# The return value is evaluated before finally runs.
def finally_order():
    x = [1]
    try:
        return x[0]
    finally:
        x[0] = 2
assert_eq(finally_order(), 1)
# finally runs on break and continue.
events = []
for i in range(2):
    try:
        if i == 0: continue
        break
    finally:
        events.append(i)
assert_eq(events, [0, 1])
# An exception raised in finally replaces the original, chaining it as context.
def replaced():
    try:
        raise KeyError("first")
    finally:
        raise ValueError("second")
e = assert_raises(ValueError, replaced)
assert_type(e.__context__, KeyError)

# except*: handlers split an exception group; unmatched parts propagate.
def star(group):
    got = []
    try:
        raise group
    except* ValueError as eg:
        got.append(("value", [str(x) for x in eg.exceptions]))
    except* TypeError as eg:
        got.append(("type", len(eg.exceptions)))
    return got
assert_eq(star(ExceptionGroup("g", [ValueError("a"), TypeError(), ValueError("b")])),
          [("value", ["a", "b"]), ("type", 1)])
# A naked exception is wrapped in a group for the handler.
def naked():
    try:
        raise ValueError("solo")
    except* ValueError as eg:
        result = type(eg).__name__, eg.message, [str(x) for x in eg.exceptions]
    return result
assert_eq(naked(), ("ExceptionGroup", "", ["solo"]))
def partial():
    try:
        raise ExceptionGroup("outer", [ValueError(), KeyError()])
    except* ValueError:
        pass
e = assert_raises(ExceptionGroup, partial)
assert_eq((e.message, [type(x) for x in e.exceptions]), ("outer", [KeyError]))
# Each handler runs at most once, with all matching leaves together.
def nested_group():
    seen = []
    try:
        raise ExceptionGroup("o", [ValueError(1), ExceptionGroup("i", [ValueError(2)])])
    except* ValueError as eg:
        seen.append(repr(eg))
    return seen
assert_eq(nested_group(), ["ExceptionGroup('o', [ValueError(1), ExceptionGroup('i', [ValueError(2)])])"])
assert_syntax_error("try:\n    pass\nexcept* ValueError:\n    pass\nexcept TypeError:\n    pass\n")
assert_syntax_error("try:\n    pass\nexcept*:\n    pass\n")
assert_syntax_error("for x in y:\n    try:\n        pass\n    except* E:\n        break\n")
assert_syntax_error("def f():\n    try:\n        pass\n    except* E:\n        return\n")
def star_group_type():
    try:
        raise ValueError
    except* ExceptionGroup:
        pass
e = assert_raises(TypeError, star_group_type)
assert_eq(str(e), "catching ExceptionGroup with except* is not allowed. Use except instead.")

# with: __enter__'s result binds to the target; __exit__ sees the exception.
class Manager:
    def __init__(self, name, log, suppress=False):
        self.name, self.log, self.suppress = name, log, suppress
    def __enter__(self):
        self.log.append(("enter", self.name))
        return self.name.upper()
    def __exit__(self, kind, value, traceback):
        self.log.append(("exit", self.name, kind))
        return self.suppress
log = []
with Manager("a", log) as a, Manager("b", log) as b:
    log.append((a, b))
assert_eq(log, [("enter", "a"), ("enter", "b"), ("A", "B"), ("exit", "b", None), ("exit", "a", None)])
# Parenthesized context managers, with a trailing comma.
log = []
with (
    Manager("x", log) as x,
    Manager("y", log, suppress=True),
):
    raise RuntimeError
assert_eq(log, [("enter", "x"), ("enter", "y"), ("exit", "y", RuntimeError), ("exit", "x", None)])
# A true __exit__ result suppresses the exception; false lets it propagate.
def propagates():
    with Manager("p", []):
        raise KeyError
assert_raises(KeyError, propagates)
# The target may be any assignment target, including a tuple.
class Pair:
    def __enter__(self): return (1, 2)
    def __exit__(self, *exc): pass
with Pair() as (first, second):
    pass
assert_eq((first, second), (1, 2))
# The context manager protocol is looked up on the type.
class NotAManager: pass
def missing():
    with NotAManager():
        pass
e = assert_raises(TypeError, missing)
assert_eq(str(e), "'NotAManager' object does not support the context manager protocol (missed __exit__ method)")
instance_only = NotAManager()
instance_only.__enter__ = lambda: None
instance_only.__exit__ = lambda *a: None
def instance_lookup():
    with instance_only:
        pass
assert_raises(TypeError, instance_lookup)
# with exits on return, break, and continue.
log = []
def early():
    with Manager("r", log):
        return "value"
assert_eq(early(), "value")
for i in range(1):
    with Manager("loop", log):
        break
assert_eq(log, [("enter", "r"), ("exit", "r", None), ("enter", "loop"), ("exit", "loop", None)])

# for and iter() name the type that cannot be iterated, and __iter__ = None blocks iteration.
class NotAnIterator:
    def __iter__(self): return 5
class Blocked:
    __iter__ = None
    def __getitem__(self, index): return index
for source, message in ((NotAnIterator(), "NotAnIterator.__iter__() must return an iterator, not int"),
                        (Blocked(), "'Blocked' object is not iterable"), (object(), "'object' object is not iterable")):
    try:
        for item in source:
            pass
    except TypeError as error:
        assert_eq(str(error), message)
    else:
        raise AssertionError("iterated " + message)
