# spec: PLS-315 13.7, 13.10, 7.4.3
# description: Between two instances, a declined method passes the
# operator or comparison to the other operand's reflected method, and a
# subclass's overriding reflected method comes before its base's own;
# methods that loop are called in that order inside functions as at
# module level, and when every one declines, the operator raises
# TypeError and == falls back to identity.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Left:
    def __add__(self, o):
        spin(); log.append(("Left.add", type(o).__name__))
        return NotImplemented
    def __sub__(self, o):
        spin(); log.append(("Left.sub", type(o).__name__))
        return "left-sub"
    def __rsub__(self, o):
        spin(); log.append(("Left.rsub", type(o).__name__))
        return NotImplemented
    def __lt__(self, o):
        spin(); log.append(("Left.lt", type(o).__name__))
        return NotImplemented
    def __gt__(self, o):
        spin(); log.append(("Left.gt", type(o).__name__))
        return NotImplemented
    def __eq__(self, o):
        spin(); log.append(("Left.eq", type(o).__name__))
        return NotImplemented

class Right:
    def __radd__(self, o):
        spin(); log.append(("Right.radd", type(o).__name__))
        return "right-radd"
    def __gt__(self, o):
        spin(); log.append(("Right.gt", type(o).__name__))
        return "right-gt"

class Sub(Left):
    def __rsub__(self, o):
        spin(); log.append(("Sub.rsub", type(o).__name__))
        return "sub-rsub"
    def __gt__(self, o):
        spin(); log.append(("Sub.gt", type(o).__name__))
        return NotImplemented

class Declining(Left):
    def __rsub__(self, o):
        spin(); log.append(("Declining.rsub", type(o).__name__))
        return NotImplemented

def operations():
    del log[:]
    left, right, sub, declining = Left(), Right(), Sub(), Declining()
    out = [left + right, left < right, left - sub, left - declining]
    n = left
    n += right
    out.append(n)
    for f in (lambda: left + left, lambda: left < left, lambda: left < declining, lambda: left < sub):
        try:
            f()
        except TypeError as e:
            out.append(str(e))
    out += [left == left, left == Left(), left != sub]
    out.append(list(log))
    return out

expected = [
    "right-radd", "right-gt", "sub-rsub", "left-sub", "right-radd",
    "unsupported operand type(s) for +: 'Left' and 'Left'",
    "'<' not supported between instances of 'Left' and 'Left'",
    "'<' not supported between instances of 'Left' and 'Declining'",
    "'<' not supported between instances of 'Left' and 'Sub'",
    True, False, True,
    [("Left.add", "Right"), ("Right.radd", "Left"),
     ("Left.lt", "Right"), ("Right.gt", "Left"),
     ("Sub.rsub", "Left"),
     ("Declining.rsub", "Left"), ("Left.sub", "Declining"),
     ("Left.add", "Right"), ("Right.radd", "Left"),
     ("Left.add", "Left"),
     ("Left.lt", "Left"), ("Left.gt", "Left"),
     ("Left.gt", "Left"), ("Left.lt", "Declining"),
     ("Sub.gt", "Left"), ("Left.lt", "Sub"),
     ("Left.eq", "Left"), ("Left.eq", "Left"),
     ("Left.eq", "Left"), ("Left.eq", "Left"),
     ("Left.eq", "Left"), ("Left.eq", "Sub")],
]
assert_eq(operations(), expected)
