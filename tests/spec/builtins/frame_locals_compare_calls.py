# spec: PLS-315 28.3, 7.2.4
# description: == and != of a FrameLocalsProxy and a dict compare the
# proxy's snapshot with the dict, each value's Python __eq__ called, which
# may loop, return a non-bool or raise; a dict on the left reflects to it.
# A dict subclass compares so too, its own Python __eq__ first.
from harness import *

log = []
class E:
    def __init__(self, answer): self.answer = answer
    def __eq__(self, other):
        for _ in range(2): pass
        log.append(self.answer)
        if self.answer == "raise": raise LookupError("eq")
        return self.answer
class S(dict): pass
class T(dict):
    def __eq__(self, other):
        for _ in range(2): pass
        log.append("T")
        return "t"
def run(f):
    del log[:]
    try:
        return f(), log[:]
    except Exception as e:
        return type(e).__name__, log[:]

def compared():
    e = E(True)
    d = host.frame().f_locals
    return [run(lambda: d == {"e": 1, "d": d}), run(lambda: d != {"e": 1, "d": d}), run(lambda: {"e": 1, "d": d} == d),
            run(lambda: d == {"e": 1}), run(lambda: d == S(e=1, d=d)), run(lambda: S(e=1, d=d) != d),
            run(lambda: d == T()), run(lambda: T() == d), (e.__setattr__("answer", "raise"), run(lambda: d == {"e": 1, "d": d}))[1]]
expected = [(True, [True]), (False, [True]), (True, [True]), (False, []), (True, [True]), (False, [True]),
            ("t", ["T"]), ("t", ["T"]), ("LookupError", ["raise"])]
assert_eq(compared(), expected)
def gen():
    yield compared()
assert_eq(next(gen()), expected)
