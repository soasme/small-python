# spec: PLS-315 23.4, 7.5.8
# description: str.format calls each field's object's __format__ with the
# field's spec, which may loop, in the order of the fields, the literal
# text and escapes around them kept: a nested spec's fields are formatted
# first, a conversion formats the converted str instead, an object
# reached by attribute or index, or passed by keyword, is formatted as
# well, a str subclass result is its text, and a result that is not a str
# raises TypeError, as does a method's exception, propagate; markup after
# a field is parsed after its call. So does str.format called on the
# class or held, and str.format_map, whose fields are its mapping's: a
# positional field raises ValueError, a missing key KeyError, unless a
# dict subclass's __missing__ answers. Inside functions as at module
# level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Text(str): pass

class Shown:
    def __init__(self, tag): self.tag = tag
    def __format__(self, spec):
        spin()
        log.append((self.tag, spec))
        if spec == "bad": raise KeyError("format")
        if spec == "int": return 5
        if spec == "sub": return Text("<sub>")
        return "<%s%s>" % (self.tag, spec)
    def __repr__(self): return "Shown(%s)" % self.tag

class Width:
    def __format__(self, spec): return ">3"

class Missing(dict):
    def __missing__(self, key): return key

class Holder:
    def __init__(self): self.field = Shown("attr")

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    a, b = Shown("a"), Shown("b")
    out = ["{}".format(a), "x{}y{:>3}z{{}}".format(a, b), "{0}{1}{0}".format(a, b), "{!r}|{}".format(a, b),
           "{:{}}".format(a, "w"), "{0.field}".format(Holder()), "[{:sub}]".format(a), "{}{}".format(1, a),
           error(lambda: "{:int}".format(a)), error(lambda: "{:bad}".format(a)), error(lambda: "{}{".format(a)),
           error(lambda: "{}{}".format(a)), "{:{}}-{}".format(a, b, Shown("c")), "{0[1]}{1[k]}".format([1, a], {"k": b}),
           "{x}{}{y:{}}".format(a, b, x=Shown("x"), y=a), "{x.field}".format(x=Holder()), "{:{}{}}|".format(a, b, "q"),
           "{:{}}|".format(7, Width())]
    shown, method = {"k": a, "n": [b]}, str.format
    out += [str.format("{}|{k}", a, k=b), method("<{}>", b), "{k}{n[0]}".format_map(shown), str.format_map("{k}", shown),
            error(lambda: "{}".format_map(shown)), error(lambda: "{x}".format_map(shown)), "{k}".format_map(Missing(k=a)), "{k}".format_map({"k": 1})]
    out.append(list(log))
    return out

expected = ["<a>", "x<a>y<b>3>z{}", "<a><b><a>", "Shown(a)|<b>", "<aw>", "<attr>", "[<sub>]", "1<a>",
            ("TypeError", "Shown.__format__() must return a str, not int"), ("KeyError", "'format'"),
            ("ValueError", "Single '{' encountered in format string"),
            ("IndexError", "Replacement index 1 out of range for positional args tuple"), "<a<b>>-<c>", "<a><b>",
            "<x><a><a<b>>", "<attr>", "<a<b>q>|", "  7|", "<a>|<b>", "<<b>>", "<a><b>", "<a>",
            ("ValueError", "Format string contains positional fields"), ("KeyError", "'x'"), "<a>", "1",
            [("a", ""), ("a", ""), ("b", ">3"), ("a", ""), ("b", ""), ("a", ""), ("b", ""), ("a", "w"), ("attr", ""),
             ("a", "sub"), ("a", ""), ("a", "int"), ("a", "bad"), ("a", ""), ("a", ""), ("b", ""), ("a", "<b>"), ("c", ""),
             ("a", ""), ("b", ""), ("x", ""), ("a", ""), ("b", ""), ("a", "<b>"), ("attr", ""), ("b", ""), ("a", "<b>q"),
             ("a", ""), ("b", ""), ("b", ""), ("a", ""), ("b", ""), ("a", ""), ("a", "")]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
