# spec: PLS-315 26.1.2, 26.2, 26.3.2, 19.3.31, 19.3.32
# description: repr(), str(), format(), str % and an f-string field of a
# dict, frozendict, set or frozenset call each key's and then its value's
# __repr__ in order, which may loop, also inside a list, tuple, dict or set
# item, and join the texts; a dict being represented shows as {...} inside
# an item's __repr__, an entry a value's __repr__ adds is shown after it,
# and an item's exception propagates and ends the outer repr too. print
# writes such a dict's repr.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Item:
    def __init__(self, tag): self.tag = tag
    def __hash__(self): return hash(self.tag)
    def __repr__(self):
        spin()
        log.append(self.tag)
        if self.tag == "bad":
            raise KeyError("bad")
        if self.tag == "self":
            return "self:" + repr(shown)
        if self.tag == "grow":
            shown["added"] = Item("new")
        return "<" + self.tag + ">"

class Sink:
    def __init__(self): self.parts = []
    def write(self, text): self.parts.append(text)

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    global shown
    del log[:]
    shown = {1: Item("a"), Item("k"): Item("v"), "s": 2}
    out = [repr(shown), str(shown), format(shown), f"{shown}", "%r" % (shown,), "%(x)s" % {"x": shown}]
    out.append((repr({Item("s")}), repr(frozenset([Item("f")])), repr(frozendict({1: Item("d")}))))
    out.append(repr([{1: [Item("l")]}, ({Item("t")},)]))
    shown = {1: Item("self")}
    out.append(repr(shown))
    shown = {1: Item("grow")}
    out.append(repr(shown))
    shown = {1: Item("o"), 2: {3: Item("bad")}}
    out.append(error(lambda: repr(shown)))
    shown[2] = {}
    out.append(repr(shown))
    sink = Sink()
    print({1: Item("p")}, {Item("q")}, file=sink)
    out.append("".join(sink.parts))
    out.append(list(log))
    return out

expected = ["{1: <a>, <k>: <v>, 's': 2}"] * 6 + [
    ("{<s>}", "frozenset({<f>})", "frozendict({1: <d>})"),
    "[{1: [<l>]}, ({<t>},)]",
    "{1: self:{...}}",
    "{1: <grow>, 'added': <new>}",
    ("KeyError", "'bad'"), "{1: <o>, 2: {}}",
    "{1: <p>} {<q>}\n",
    ["a", "k", "v"] * 6 + ["s", "f", "d", "l", "t", "self", "grow", "new", "o", "bad", "o", "p", "q"]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
