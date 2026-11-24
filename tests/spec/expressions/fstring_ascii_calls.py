# spec: PLS-315 7.2.5, 27.1.1
# description: An f-string field's !a conversion is ascii() of its value:
# a Python __repr__, which may loop, runs once, its non-ASCII text escaped
# and a str subclass it returns kept when ASCII, before the field's
# format spec applies; a result that is not a str raises TypeError, and an
# exception from __repr__ propagates.
from harness import *

log = []
def spin():
    for _ in range(2): pass
class Shown:
    def __init__(self, text): self.text = text
    def __repr__(self):
        spin(); log.append(self.text)
        if self.text == "fail": raise LookupError("repr")
        return self.text
class Sub(str): pass

def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def cases():
    return [run(lambda: f"<{Shown('caf\xe9')!a}>"), run(lambda: f"{Shown('ab')!a:>4}"), run(lambda: f"{Shown(5)!a}"),
            run(lambda: f"{Shown('fail')!a}"), run(lambda: type(f"{Shown(Sub('x'))!a}").__name__),
            run(lambda: f"{[Shown('ŝ')]!a}")]
expected = [("<caf\\xe9>", ["caf\xe9"]), ("  ab", ["ab"]), (("TypeError", "Shown.__repr__() must return a str, not int"), [5]),
            (("LookupError", "repr"), ["fail"]), ("str", ["x"]), ("[\\u015d]", ["ŝ"])]
assert_eq(cases(), expected)
assert_eq(cases(), expected)
