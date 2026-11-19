# spec: PLS-315 25.5.3, 25.1.4
# description: ordering two lists or tuples finds the first unequal pair by
# == and decides by that pair's ordering method, a Python __lt__ or __gt__
# of a subclass of int or str among them, its == the builtin's, equal
# pairs before it skipped; a list or tuple subclass's instances compare
# their items so, and so do a sort's keys holding them. Inside functions
# and generators as at module level.
from harness import *
log = []
class W(int):
    def __lt__(self, other):
        for _ in (): pass
        log.append(("lt", int(self), int(other)))
        return int.__lt__(self, other)
    def __gt__(self, other):
        for _ in (): pass
        log.append(("gt", int(self), int(other)))
        return int.__gt__(self, other)
class T(str):
    def __lt__(self, other):
        for _ in (): pass
        log.append(("tlt", str(self), str(other)))
        return str.__lt__(self, other)
class L(list): pass
class U(tuple): pass
def run(f):
    del log[:]
    return f(), list(log)
def sort_run(f):
    # Which comparisons a sort makes is implementation-defined (Annex D).
    del log[:]
    return f(), bool(log)
def cases():
    return [run(lambda: [W(1), 2] < [W(2), 1]), run(lambda: [W(1), 5] < [W(1), 3]), run(lambda: [W(1), W(5)] <= [W(1), W(3)]),
            run(lambda: (W(1), W(2)) > (W(1), W(1))), run(lambda: [W(2)] < [3]), run(lambda: [3] > [W(2)]),
            run(lambda: (T("a"), 1) < (T("b"), 0)), run(lambda: [T("a"), T("b")] < [T("a"), T("c")]),
            run(lambda: L([W(3)]) < L([W(4)])), run(lambda: U((W(1), 2)) >= U((W(1), 1))), run(lambda: [W(1)] == [W(1)]),
            sort_run(lambda: [int(t[0][0]) for t in sorted([(L([W(i), i]),) for i in (3, 1, 2)])]),
            sort_run(lambda: [int(t[0]) for t in sorted([L([W(i), i]) for i in (3, 1, 2)])]),
            sort_run(lambda: [int(t[1]) for t in sorted([(W(1), W(i)) for i in (2, 1)])])]
def gen():
    yield cases()
expected = [(True, [('lt', 1, 2)]),
            (False, []),
            (False, []),
            (True, [('gt', 2, 1)]),
            (True, [('lt', 2, 3)]),
            (True, [('lt', 2, 3)]),
            (True, [('tlt', 'a', 'b')]),
            (True, [('tlt', 'b', 'c')]),
            (True, [('lt', 3, 4)]),
            (True, []),
            (True, []),
            ([1, 2, 3], True),
            ([1, 2, 3], True),
            ([1, 2], True)]
assert_eq(cases(), expected)
assert_eq(next(gen()), expected)
def outer():
    return cases()
assert_eq(outer(), expected)
