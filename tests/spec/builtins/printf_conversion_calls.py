# spec: PLS-315 23.6, 7.5.5, 7.5.6
# description: str % values converts each %s, %r and %a argument by its
# class's Python __str__ or __repr__, which may loop, in the order of the
# conversions, from a single value, a tuple or a mapping's keys, also in
# an augmented assignment, and a list or tuple argument by its items'
# Python __repr__ in order; widths, precisions and * arguments apply to
# the text, %a escapes it, a result that is not a str raises TypeError,
# and an error stops the formatting before the conversions after it.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class K:
    def __init__(self, v): self.v = v
    def __str__(self): spin(); log.append("s%d" % self.v); return "k%d" % self.v
    def __repr__(self): spin(); log.append("r%d" % self.v); return "K%d" % self.v
class Accent:
    def __repr__(self): spin(); log.append("a"); return "é"
class Text(str): pass
class Sub:
    def __str__(self): spin(); return Text("t")
class Keys(dict): pass

a, b = K(1), K(2)
def check(expression, value, calls):
    log.clear()
    assert_eq(expression(), value)
    assert_eq(log, calls)

def main():
    check(lambda: "%s" % a, "k1", ["s1"])
    check(lambda: "<%r>" % a, "<K1>", ["r1"])
    check(lambda: "%s-%r-%s" % (a, b, "x"), "k1-K2-x", ["s1", "r2"])
    check(lambda: "%r %d %s" % (b, 7, a), "K2 7 k1", ["r2", "s1"])
    check(lambda: "%(x)s/%(y)r/%(x)r" % {"x": a, "y": b}, "k1/K2/K1", ["s1", "r2", "r1"])
    check(lambda: "%(x)s" % Keys(x=b), "k2", ["s2"])
    check(lambda: "[%5s|%-4r|%.1s]" % (a, b, a), "[   k1|K2  |k]", ["s1", "r2", "s1"])
    check(lambda: "%*s|%-*.*r" % (4, a, 3, 1, b), "  k1|K  ", ["s1", "r2"])
    check(lambda: "%a %a" % (Accent(), a), "\\xe9 K1", ["a", "r1"])
    check(lambda: "%-6a|%.3a" % (Accent(), Accent()), "\\xe9  |\\xe", ["a", "a"])
    check(lambda: "%(e)a" % {"e": Accent()}, "\\xe9", ["a"])
    check(lambda: "%s%%" % (Sub(),), "t%", [])
    check(lambda: "%s" % (a,) + "%s" % b, "k1k2", ["s1", "s2"])
    def loop():
        return [("%s:%r" % (v, v)) for v in (a, b)]
    check(loop, ["k1:K1", "k2:K2"], ["s1", "r1", "s2", "r2"])
    def inplace():
        text = "<%s>"
        text %= a
        return text
    check(inplace, "<k1>", ["s1"])
    def gen():
        yield "%s" % a
        yield "%r" % (b,)
    check(lambda: list(gen()), ["k1", "K2"], ["s1", "r2"])
    # A list's or tuple's items convert by their __repr__.
    check(lambda: "%s" % [a, "x", b], "[K1, 'x', K2]", ["r1", "r2"])
    check(lambda: "%s|%r|%s" % ([b], (a,), a), "[K2]|(K1,)|k1", ["r2", "r1", "s1"])
    check(lambda: "%a|%-8s|%.3r" % ([Accent()], (a, 1), [b]), "[\\xe9]|(K1, 1) |[K2", ["a", "r1", "r2"])
    check(lambda: "%(x)s" % {"x": [a]}, "[K1]", ["r1"])
    def listed():
        text = "<%s>"
        text %= [b]
        return text
    check(listed, "<[K2]>", ["r2"])
    def gen_list():
        yield "%s" % ([a],)
    check(lambda: list(gen_list()), ["[K1]"], ["r1"])
    nested = [a]
    nested.append(nested)
    check(lambda: "%s" % [nested], "[[K1, [...]]]", ["r1"])
main()

# A method's error, or a result that is not a str, stops at its conversion;
# too few or too many arguments are found after the conversions before.
class Wrong:
    def __str__(self): spin(); return 1
class WrongRepr:
    def __repr__(self): spin(); return b"x"
class Raising:
    def __repr__(self): spin(); log.append("raise"); raise KeyError("k")
assert_raises(TypeError, lambda: "%s" % Wrong(), message="Wrong.__str__() must return a str, not int")
assert_raises(TypeError, lambda: "%r" % (WrongRepr(),), message="WrongRepr.__repr__() must return a str, not bytes")
assert_raises(TypeError, lambda: "%a" % WrongRepr(), message="WrongRepr.__repr__() must return a str, not bytes")
assert_raises(TypeError, lambda: "%s" % [WrongRepr()], message="WrongRepr.__repr__() must return a str, not bytes")
log.clear()
assert_raises(KeyError, lambda: "%s %s" % ([a, Raising(), b], a), message="'k'")
assert_eq(log, ["r1", "raise"])
log.clear()
assert_raises(KeyError, lambda: "%r %s" % (Raising(), a), message="'k'")
assert_eq(log, ["raise"])
log.clear()
assert_raises(TypeError, lambda: "%s %s" % (a,), message="not enough arguments for format string (got 1)")
assert_eq(log, ["s1"])
log.clear()
assert_raises(TypeError, lambda: "%s" % (a, b), message="not all arguments converted during string formatting (required 1, got 2)")
assert_eq(log, ["s1"])
log.clear()
assert_raises(TypeError, lambda: "%s %d" % (a, b), message="format argument 2: %d requires a real number, not K")
assert_eq(log, ["s1"])
