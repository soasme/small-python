# spec: PLS-315 15.4.3, 21.4.3
# description: except* of a group splits it by calling its split method
# with the clause's types: a group's own split calls a subclass's Python
# derive for each part it makes, a subclass's Python split, or one a
# property gives, is called instead, and its pair is the match the
# clause handles and the rest the next clause splits, by its own split. A
# split returning no tuple, or a tuple of fewer than two items, raises
# TypeError; an error of the split propagates from the try statement.
from harness import *

log = []

class Derived(ExceptionGroup):
    def derive(self, excs):
        for _ in (): pass
        log.append(("derive", len(excs)))
        return Derived(self.message, excs)

class Splits(ExceptionGroup):
    def split(self, condition):
        log.append(("split", condition.__name__))
        return super().split(condition)

def gives(result):
    def get(self):
        log.append("read")
        return lambda condition: result
    return property(get)

Odd = type("Odd", (ExceptionGroup,), {"split": gives(5)})
Short = type("Short", (ExceptionGroup,), {"split": gives((None,))})

class Raises(ExceptionGroup):
    def split(self, condition):
        raise KeyError("split")

def handle(group):
    for _ in (): pass
    seen = []
    try:
        try:
            raise group
        except* ValueError as e:
            seen.append(("value", type(e).__name__, len(e.exceptions)))
        except* TypeError as e:
            seen.append(("type", type(e).__name__, len(e.exceptions)))
    except Exception as e:
        seen.append(("left", type(e).__name__, str(e)))
    return seen

def results():
    del log[:]
    out = [handle(Derived("d", [ValueError(1), TypeError(2), KeyError(3)])),
           handle(Splits("s", [ValueError(1), TypeError(2)])),
           handle(Odd("o", [ValueError(1)])),
           handle(Short("h", [ValueError(1)])),
           handle(Raises("r", [ValueError(1)]))]
    return out, list(log)

expected = ([[("value", "Derived", 1), ("type", "Derived", 1), ("left", "Derived", "d (1 sub-exception)")],
             [("value", "ExceptionGroup", 1), ("type", "ExceptionGroup", 1)],
             [("left", "TypeError", "Odd.split must return a tuple, not int")],
             [("left", "TypeError", "Short.split must return a 2-tuple, got tuple of size 1")],
             [("left", "KeyError", "'split'")]],
            [("derive", 1), ("derive", 2), ("derive", 1), ("derive", 1), ("derive", 1),
             ("split", "ValueError"), "read", "read"])

assert_eq(results(), expected)
assert_eq(results(), expected)
