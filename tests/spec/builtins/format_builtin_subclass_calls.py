# spec: PLS-315 7.5.8, 23.4
# description: str.format of an instance of a builtin type's subclass calls
# its class's Python __format__, which may loop, given the spec; one keeping
# the builtin __format__ formats by an empty spec as str() does, calling a
# Python __str__, and by any other spec its builtin value without it. A
# __format__ returning a non-str raises TypeError.
from harness import *

log = []
def spin():
    for _ in range(2): pass
class J(int):
    def __format__(self, spec):
        spin(); log.append(("format", spec)); return str(int(self) * 2) + spec
class S(str):
    def __str__(self):
        spin(); log.append("str"); return "overridden"
class F(float):
    def __str__(self):
        spin(); log.append("str"); return "f"
class Bad(int):
    def __format__(self, spec): spin(); return 5

def run(f):
    del log[:]
    try:
        return f(), log[:]
    except Exception as e:
        return (type(e).__name__, str(e)), log[:]

def cases():
    return [run(lambda: "{0}|{0:x}".format(J(10))), run(lambda: "{}".format(S("ab"))), run(lambda: "{:>4}".format(S("ab"))),
            run(lambda: "{0}{0:.1f}".format(F(1.25))), run(lambda: "{k}".format(k=S("q"))), run(lambda: "{0}".format(Bad(1)))]
expected = [("20|20x", [("format", ""), ("format", "x")]), ("overridden", ["str"]), ("  ab", []), ("f1.2", ["str"]),
            ("overridden", ["str"]), (("TypeError", "Bad.__format__() must return a str, not int"), [])]
assert_eq(cases(), expected)
def gen():
    yield cases()
assert_eq(next(gen()), expected)
