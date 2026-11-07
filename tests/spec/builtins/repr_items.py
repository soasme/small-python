# spec: PLS-315 25.1.2, 25.2, 19.3.31, 19.3.32
# description: repr(), str(), format() and an f-string field of a list or
# tuple call each item's __repr__ in order, which may loop, and join the
# texts; a list or tuple being represented shows as [...] or (...) inside an
# item's __repr__ and again normally once it is done, also after an item's
# exception propagated. Items added or removed meanwhile, also by a native
# __repr__ before them, are seen as the items are read by index; a __repr__
# returning no str raises TypeError; a str subclass's text is joined. print
# writes such a list's repr, inside functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Item:
    def __init__(self, tag): self.tag = tag
    def __repr__(self):
        spin()
        log.append(self.tag)
        if self.tag == "bad":
            raise KeyError("bad")
        if self.tag == "self":
            return "self:" + repr(shown) + "/" + repr(pair)
        if self.tag == "grow":
            shown.append(Item("added"))
        if self.tag == "shrink":
            del shown[-1]
        return "<" + self.tag + ">"

class Wrong:
    def __repr__(self):
        spin()
        return 1

class Text(str): pass

class Sub:
    def __repr__(self):
        spin()
        return Text("sub")

class Plain: pass

class Remover:
    __repr__ = staticmethod(lambda: (shown.pop(), "removed")[1])

class Raiser:
    __repr__ = staticmethod(lambda: 1 // 0)

class Sink:
    def __init__(self): self.parts = []
    def write(self, text): self.parts.append(text)

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    global shown, pair
    del log[:]
    shown = [Item("a"), 1, "s", Item("b")]
    pair = (Item("t"),)
    out = [repr(shown), str(shown), format(shown), f"{shown}", f"{shown!r}", repr(pair), str(()), repr([])]
    shown = [Item("x"), [Item("nested")], (Item("y"), 2)]
    out.append(repr(shown))
    shown = [Item("self")]
    pair = (Item("p"), shown)
    out.append(repr(shown))
    out.append(repr(pair))
    shown = [Item("bad"), Item("never")]
    out.append(error(lambda: repr(shown)))
    shown[0] = 0
    out.append(repr(shown))
    shown = [Raiser(), Item("z")]
    out.append(error(lambda: repr(shown)))
    shown[0] = "r"
    out.append(repr(shown))
    shown = [Remover(), Item("popped")]
    out.append(repr(shown))
    shown = [Item("grow"), Item("g2")]
    out.append(repr(shown))
    shown = [Item("shrink"), Item("s2"), Item("gone")]
    out.append(repr(shown))
    out.append(error(lambda: repr([Wrong()])))
    out.append(repr([Sub(), Sub()]))
    text = repr([Plain()])
    out.append((text[:2], "Plain object at" in text, text[-2:]))
    sink = Sink()
    print([Item("p1")], "and", (Item("p2"),), file=sink)
    out.append("".join(sink.parts))
    out.append(list(log))
    return out

expected = ["[<a>, 1, 's', <b>]", "[<a>, 1, 's', <b>]", "[<a>, 1, 's', <b>]", "[<a>, 1, 's', <b>]",
            "[<a>, 1, 's', <b>]", "(<t>,)", "()", "[]",
            "[<x>, [<nested>], (<y>, 2)]",
            "[self:[...]/(<p>, [...])]",
            "(<p>, [self:[...]/(...)])",
            ("KeyError", "'bad'"),
            "[0, <never>]",
            ("ZeroDivisionError", "division by zero"), "['r', <z>]", "[removed]",
            "[<grow>, <g2>, <added>]",
            "[<shrink>, <s2>]",
            ("TypeError", "Wrong.__repr__() must return a str, not int"),
            "[sub, sub]",
            ("[<", True, ">]"),
            "[<p1>] and (<p2>,)\n",
            ["a", "b", "a", "b", "a", "b", "a", "b", "a", "b", "t",
             "x", "nested", "y",
             "self", "p", "p", "self", "bad", "never", "z", "grow", "g2", "added", "shrink", "s2",
             "p1", "p2"]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
