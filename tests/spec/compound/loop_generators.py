# spec: PLS-315 27.2.1, 7.7
# description: A for loop resumes a generator by GeneratorResume: its state
# runs and suspends, its return ends the loop, and what it raises reaches the
# loop with StopIteration made a RuntimeError.
from harness import *

def count(n):
    i = 0
    while i < n:
        yield i
        i += 1
    return "done"

# Each item is the next yield; the return value ends the loop silently.
assert_eq([x for x in count(4)], [0, 1, 2, 3])
total = 0
for x in count(5):
    total += x
assert_eq(total, 10)
def summed(n):
    total = 0
    for x in count(n):
        total += x
    return total
assert_eq(summed(5), 10)

# The generator runs while the loop resumes it, and is closed after.
def watch():
    yield g.gi_running
    yield g.gi_frame is not None
g = watch()
assert_eq(list(g), [True, True])
assert_eq(g.gi_running, False)
assert_eq(g.gi_frame, None)

# A loop may stop early; the generator stays suspended, then resumes.
g = count(10)
for x in g:
    if x == 2:
        break
assert_eq(next(g), 3)

# Nested generators, each resumed by the other's loop.
def doubled(it):
    for x in it:
        yield 2 * x
def nested(n):
    for y in doubled(count(n)):
        yield y + 1
assert_eq(list(nested(3)), [1, 3, 5])

# An exception from the body reaches the loop's handler.
def failing():
    yield 1
    raise KeyError("k")
seen = []
try:
    for x in failing():
        seen.append(x)
except KeyError as e:
    seen.append(e.args[0])
assert_eq(seen, [1, "k"])

# StopIteration raised in a generator becomes a RuntimeError, chained.
def stopping():
    yield 1
    raise StopIteration("early")
e = assert_raises(RuntimeError, lambda: [x for x in stopping()])
assert_eq(str(e), "generator raised StopIteration")
assert_eq(type(e.__cause__), StopIteration)

# The handled exception inside the generator is its own, not the loop's.
def context():
    yield repr(__import__ and None)
    try:
        raise ValueError("inner")
    except ValueError:
        yield "handling"
    yield "after"
log = []
try:
    raise TypeError("outer")
except TypeError:
    for x in context():
        log.append(x)
assert_eq(log, ["None", "handling", "after"])

# A generator running when the loop resumes it raises ValueError.
def again():
    for x in me:
        yield x
    yield 0
me = again()
e = assert_raises(ValueError, lambda: next(me))
assert_eq(str(e), "generator already executing")

# A generator that delegates is resumed through yield from.
def delegating():
    yield from count(2)
    yield from count(1)
assert_eq([x for x in delegating()], [0, 1, 0])
