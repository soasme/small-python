# spec: PLS-315 7.4.4
# description: A built-in's report of a keyword naming no keyword parameter
# compares each keyword with the parameter names in order by p == key, so a
# str subclass key's Python __eq__ is called with each name in turn until
# it returns a true value: the first keyword equal to none is unexpected,
# with its suggestion, and when every keyword equals one the keywords are
# invalid; an exception from __eq__ propagates from the call. Inside
# functions and generators as at module level.
from harness import *

log = []

class Key(str):
    __hash__ = str.__hash__
    def __eq__(self, other):
        for _ in range(2): pass
        log.append((str(self), other))
        if str(self) == "boom": raise LookupError(other)
        return str(self) == "any" or str(self) + "!" == other + "!"

def message(call, keywords):
    try:
        call(keywords)
    except TypeError as e:
        return str(e)
    return None

def report(call, *names):
    del log[:]
    text = message(call, {Key(n): 1 for n in names})
    return text, list(log)

print_call = lambda k: print(0, **k)
assert_eq(report(print_call, "sepp"), ("print() got an unexpected keyword argument 'sepp'. Did you mean 'sep'?",
          [("sepp", "sep"), ("sepp", "end"), ("sepp", "file"), ("sepp", "flush")]))
assert_eq(report(print_call, "any"), ("invalid keyword argument for print()", [("any", "sep")]))
assert_eq(report(print_call, "any", "zz")[0], "print() got an unexpected keyword argument 'zz'")
assert_eq(report(print_call, "any", "zz")[1], [("any", "sep"), ("zz", "sep"), ("zz", "end"), ("zz", "file"), ("zz", "flush")])
assert_eq(report(lambda k: sorted([], **k), "kee"), ("sort() got an unexpected keyword argument 'kee'. Did you mean 'key'?",
          [("kee", "key"), ("kee", "reverse")]))
assert_eq(report(lambda k: min([1], **k), "defalt")[0], "min() got an unexpected keyword argument 'defalt'. Did you mean 'default'?")
assert_eq(report(lambda k: property(**k), "any")[0], "invalid keyword argument for property()")
assert_eq(report(lambda k: sentinel("s", **k), "rpr"), ("sentinel() got an unexpected keyword argument 'rpr'. Did you mean 'repr'?",
          [("rpr", "repr")]))
assert_eq(report(lambda k: round(1, **k), "ndigit")[0], "round() got an unexpected keyword argument 'ndigit'. Did you mean 'ndigits'?")

del log[:]
e = assert_raises(LookupError, lambda: print(0, **{Key("boom"): 1}))
assert_eq(e.args, ("sep",))
assert_eq(log, [("boom", "sep")])

def inside():
    return report(print_call, "sepp")[0]
assert_eq(inside(), "print() got an unexpected keyword argument 'sepp'. Did you mean 'sep'?")

def gen():
    yield report(lambda k: sorted([], **k), "kee")[0]
    yield report(print_call, "any")[0]
assert_eq(list(gen()), ["sort() got an unexpected keyword argument 'kee'. Did you mean 'key'?", "invalid keyword argument for print()"])
