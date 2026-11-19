# spec: PLS-315 7.6.2, 14.3
# description: A builtin value, or a builtin subclass's instance, whose
# builtin has no method for a binary operator, or a set's set operator, a
# dict's | or a frozendict's | given a plain instance, declines it: the
# instance's reflected method, which may loop, is called with the value
# itself, its result the operation's; in place too, but a dict's |= takes
# any iterable. When the reflected method declines as well, TypeError
# names the operator, at module level and inside functions alike; a
# subclass's builtin does not call the declining method again.
from harness import *

log = []

class Q:
    def __init__(self, answer): self.answer = answer
    def reply(self, name, other):
        for _ in range(2): pass
        log.append((name, type(other).__name__))
        if self.answer == "raise": raise LookupError(name)
        return NotImplemented if self.answer == "no" else (name, self.answer)
    def __ror__(self, o): return self.reply("ror", o)
    def __rand__(self, o): return self.reply("rand", o)
    def __rsub__(self, o): return self.reply("rsub", o)
    def __rxor__(self, o): return self.reply("rxor", o)
    def __rtruediv__(self, o): return self.reply("rtruediv", o)

class SubSet(set): pass
class SubList(list): pass
class SubDict(dict): pass

def run(f):
    try: return f()
    except Exception as e: return type(e).__name__ + ": " + str(e)

def inplace_or(x, y):
    x |= y
    return x
def inplace_sub(x, y):
    x -= y
    return x
def inplace_xor(x, y):
    x ^= y
    return x

def results(a):
    q = Q(a)
    return [run(lambda: {1} | q), run(lambda: frozenset() & q), run(lambda: {1} - q), run(lambda: {1} ^ q),
            run(lambda: frozendict(a=1) | q), run(lambda: {"a": 1} | q), run(lambda: [1] - q), run(lambda: "s" / q),
            run(lambda: inplace_or({1}, q)), run(lambda: inplace_xor(frozenset(), q)), run(lambda: inplace_or(SubSet(), q)),
            run(lambda: inplace_sub(SubList(), q)), run(lambda: inplace_sub(SubDict(), q)), run(lambda: inplace_or(frozendict(), q)),
            run(lambda: inplace_or({}, q))]

assert_eq(results("y"), [("ror", "y"), ("rand", "y"), ("rsub", "y"), ("rxor", "y"), ("ror", "y"), ("ror", "y"),
                         ("rsub", "y"), ("rtruediv", "y"), ("ror", "y"), ("rxor", "y"), ("ror", "y"), ("rsub", "y"),
                         ("rsub", "y"), ("ror", "y"), "TypeError: 'Q' object is not iterable"])
assert_eq(log, [("ror", "set"), ("rand", "frozenset"), ("rsub", "set"), ("rxor", "set"), ("ror", "frozendict"), ("ror", "dict"),
                ("rsub", "list"), ("rtruediv", "str"), ("ror", "set"), ("rxor", "frozenset"), ("ror", "SubSet"), ("rsub", "SubList"),
                ("rsub", "SubDict"), ("ror", "frozendict")])
del log[:]
assert_eq(results("no"), ["TypeError: unsupported operand type(s) for |: 'set' and 'Q'",
                          "TypeError: unsupported operand type(s) for &: 'frozenset' and 'Q'",
                          "TypeError: unsupported operand type(s) for -: 'set' and 'Q'",
                          "TypeError: unsupported operand type(s) for ^: 'set' and 'Q'",
                          "TypeError: unsupported operand type(s) for |: 'frozendict' and 'Q'",
                          "TypeError: unsupported operand type(s) for |: 'dict' and 'Q'",
                          "TypeError: unsupported operand type(s) for -: 'list' and 'Q'",
                          "TypeError: unsupported operand type(s) for /: 'str' and 'Q'",
                          "TypeError: unsupported operand type(s) for |=: 'set' and 'Q'",
                          "TypeError: unsupported operand type(s) for ^=: 'frozenset' and 'Q'",
                          "TypeError: unsupported operand type(s) for |=: 'SubSet' and 'Q'",
                          "TypeError: unsupported operand type(s) for -=: 'SubList' and 'Q'",
                          "TypeError: unsupported operand type(s) for -=: 'SubDict' and 'Q'",
                          "TypeError: unsupported operand type(s) for |=: 'frozendict' and 'Q'",
                          "TypeError: 'Q' object is not iterable"])
assert_eq(len(log), 14)
assert_eq(run(lambda: {1} | Q("raise")), "LookupError: ror")

def gen():
    yield {1} | Q("g")
    x = SubList()
    x -= Q("g")
    yield x
assert_eq(list(gen()), [("ror", "g"), ("rsub", "g")])
