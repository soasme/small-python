# spec: PLS-315 27.1.3
# description: a callable iterator iter(f, sentinel) of a Python function
# f, which may loop, or of a builtin's, calls f for each item a for loop, a comprehension, a
# consumer such as list() or sum(), or next() takes, comparing the result
# with the sentinel: an equal one ends it for good, a StopIteration from f
# exhausts it, another error propagates and leaves it; a call of f that
# itself exhausts the iterator ends it, its own value dropped. Inside
# functions as at module level.
from harness import *

log = []

def counter():
    n = [0]
    def f():
        for _ in (): pass
        n[0] += 1
        log.append(n[0])
        return n[0]
    return f

def takes():
    out = []
    out.append([x for x in iter(counter(), 3)])
    out.append(list(iter(counter(), 2)))
    it = iter(counter(), 2)
    out.append((next(it), next(it, "d"), next(it, "e")))
    it = iter(counter(), 9)
    for x in it:
        if x == 2: break
    out.append(next(it))
    out.append(sum(iter(counter(), 4)))
    class Eq:
        def __eq__(self, o):
            log.append("eq")
            return o == 2
    out.append(list(iter(counter(), Eq())))
    return out, log[:]

assert_eq(takes(), ([[1, 2], [1], (1, "d", "e"), 3, 6, [1]],
                    [1, 2, 3, 1, 2, 1, 2, 1, 2, 3, 1, 2, 3, 4, 1, "eq", 2, "eq"]))

def ends():
    out = []
    def stops():
        for _ in (): pass
        raise StopIteration
    it = iter(stops, 0)
    out.append((list(it), list(it)))
    calls = [0]
    def bad():
        for _ in (): pass
        calls[0] += 1
        if calls[0] == 2: raise KeyError("b")
        return calls[0]
    it = iter(bad, 0)
    try: list(it)
    except KeyError as e: out.append(e.args)
    out.append(next(it))
    def spam():
        for _ in (): pass
        if spam.again: return 2
        spam.again = True
        list(spam.iterator)
        return 1
    spam.again = False
    spam.iterator = iter(spam, 2)
    out.append([x for x in spam.iterator])
    return out

assert_eq(ends(), [([], []), ("b",), 3, []])

# A builtin's function ends the iterator by StopIteration, and its other
# exceptions propagate.
def natives():
    out = [list(iter(iter([1, 2]).__next__, 0))]
    try: list(iter([1].pop, None))
    except IndexError as e: out.append(str(e))
    return out

assert_eq(natives(), [[1, 2], "pop from empty list"])

# A builtin callable's StopIteration ends the iterator, and another error
# propagates, whatever takes its items: a starred display, unpacking,
# zip(), any() and all().
def builtin_nexts(): return iter(iter([1, 2]).__next__, None)
def taken():
    out = [[*builtin_nexts()]]
    a, b = builtin_nexts(); out.append((a, b))
    out.append(list(zip(builtin_nexts(), builtin_nexts())))
    out.append((any(builtin_nexts()), all(builtin_nexts())))
    try: [*iter([].pop, None)]
    except IndexError as e: out.append(str(e))
    return out
assert_eq(taken(), [[1, 2], (1, 2), [(1, 1), (2, 2)], (True, True), "pop from empty list"])
