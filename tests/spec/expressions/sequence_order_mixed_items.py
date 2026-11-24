# spec: PLS-315 25.5.3, 7.2.4
# description: Ordering two lists or tuples whose first unequal items are an
# instance and a container calls the instance's Python ordering method,
# which may loop, mutate either sequence or return NotImplemented, or the
# reflected one when the container comes first; NotImplemented from both
# raises TypeError, and other errors propagate.
from harness import *

log = []
class A:
    def __init__(self, answer): self.answer = answer
    def __lt__(self, other):
        for _ in range(2): pass
        log.append(("lt", type(other).__name__))
        if self.answer == "clear": other.clear(); return NotImplemented
        if self.answer == "raise": raise LookupError("lt")
        return self.answer
    def __gt__(self, other):
        for _ in range(2): pass
        log.append(("gt", type(other).__name__))
        return self.answer

def run(f):
    del log[:]
    try:
        return f(), log[:]
    except Exception as e:
        return (type(e).__name__, str(e)), log[:]

def cases():
    nested = [[A("clear")]]
    return [run(lambda: [A(True)] < [[1]]), run(lambda: (1, A("yes")) < (1, (2,))), run(lambda: [[1]] < [A(False)]),
            run(lambda: (nested[0] < nested, nested)), run(lambda: [A("raise")] < [{}]),
            run(lambda: [A(NotImplemented)] < [[1]])]
expected = [(True, [("lt", "list")]), ("yes", [("lt", "tuple")]), (False, [("gt", "list")]),
            (("TypeError", "'<' not supported between instances of 'A' and 'list'"), [("lt", "list")]),
            (("LookupError", "lt"), [("lt", "dict")]),
            (("TypeError", "'<' not supported between instances of 'A' and 'list'"), [("lt", "list")])]
assert_eq(cases(), expected)
def gen():
    yield cases()
assert_eq(next(gen()), expected)
