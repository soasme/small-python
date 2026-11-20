# spec: PLS-315 21.3.6, 21.1.2, 21.3.3, 21.3.4
# description: a Unicode error's str converts its reason, then its encoding
# read after it, by their Python __str__, writing a str subclass's
# characters without converting them again; an unset one is "<NULL>"; the
# object is checked only after both, unset or of the wrong type a
# TypeError. Deleting an exception's field unsets it: it reads as None and
# the texts and reductions showing set fields leave it out.
from harness import *

log = []
class S:
    def __init__(self, t, bad=None):
        self.t, self.bad = t, bad
    def __str__(self):
        for _ in (): pass
        log.append(self.t)
        if self.bad == "raise": raise ValueError(self.t)
        if self.bad == "int": return 3
        if self.bad == "none": exc.object = None
        if self.bad == "del": del exc.object
        if self.bad == "enc": exc.encoding = S("late")
        return "<" + self.t + ">"
class Evil(str):
    def __str__(self):
        log.append("evil")
        return self
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, list(log)
def made(kind, reason, encoding=None):
    global exc
    exc = (UnicodeEncodeError("x", "ab\u20ac", 2, 3, "z") if kind == "E" else
           UnicodeDecodeError("x", b"abc", 0, 2, "z") if kind == "D" else UnicodeTranslateError("ab", 0, 1, "z"))
    exc.reason = reason
    if kind != "T": exc.encoding = encoding
    return exc
def deleted(e, *names):
    for name in names: delattr(e, name)
    return e
def gen():
    yield str(made("E", S("in"), S("gen")))
assert_eq(run(lambda: str(made("E", "plain", "utf-8"))), ("'utf-8' codec can't encode character '\\u20ac' in position 2: plain", []))
assert_eq(run(lambda: str(made("D", "plain", "utf-8"))), ("'utf-8' codec can't decode bytes in position 0-1: plain", []))
assert_eq(run(lambda: str(made("E", "plain", S("e")))), ("'<e>' codec can't encode character '\\u20ac' in position 2: plain", ['e']))
assert_eq(run(lambda: str(made("D", "plain", S("e")))), ("'<e>' codec can't decode bytes in position 0-1: plain", ['e']))
assert_eq(run(lambda: str(made("E", "plain", S("e", "raise")))), (('ValueError', 'e'), ['e']))
assert_eq(run(lambda: str(made("D", "plain", S("e", "raise")))), (('ValueError', 'e'), ['e']))
assert_eq(run(lambda: str(made("E", "plain", Evil("u8")))), ("'u8' codec can't encode character '\\u20ac' in position 2: plain", ['evil']))
assert_eq(run(lambda: str(made("D", "plain", Evil("u8")))), ("'u8' codec can't decode bytes in position 0-1: plain", ['evil']))
assert_eq(run(lambda: str(made("T", "plain"))), ("can't translate character '\\x61' in position 0: plain", []))
assert_eq(run(lambda: str(made("E", S("r"), "utf-8"))), ("'utf-8' codec can't encode character '\\u20ac' in position 2: <r>", ['r']))
assert_eq(run(lambda: str(made("D", S("r"), "utf-8"))), ("'utf-8' codec can't decode bytes in position 0-1: <r>", ['r']))
assert_eq(run(lambda: str(made("E", S("r"), S("e")))), ("'<e>' codec can't encode character '\\u20ac' in position 2: <r>", ['r', 'e']))
assert_eq(run(lambda: str(made("D", S("r"), S("e")))), ("'<e>' codec can't decode bytes in position 0-1: <r>", ['r', 'e']))
assert_eq(run(lambda: str(made("E", S("r"), S("e", "raise")))), (('ValueError', 'e'), ['r', 'e']))
assert_eq(run(lambda: str(made("D", S("r"), S("e", "raise")))), (('ValueError', 'e'), ['r', 'e']))
assert_eq(run(lambda: str(made("E", S("r"), Evil("u8")))), ("'u8' codec can't encode character '\\u20ac' in position 2: <r>", ['r', 'evil']))
assert_eq(run(lambda: str(made("D", S("r"), Evil("u8")))), ("'u8' codec can't decode bytes in position 0-1: <r>", ['r', 'evil']))
assert_eq(run(lambda: str(made("T", S("r")))), ("can't translate character '\\x61' in position 0: <r>", ['r']))
assert_eq(run(lambda: str(made("E", S("r", "raise"), "utf-8"))), (('ValueError', 'r'), ['r']))
assert_eq(run(lambda: str(made("D", S("r", "raise"), "utf-8"))), (('ValueError', 'r'), ['r']))
assert_eq(run(lambda: str(made("E", S("r", "raise"), S("e")))), (('ValueError', 'r'), ['r']))
assert_eq(run(lambda: str(made("D", S("r", "raise"), S("e")))), (('ValueError', 'r'), ['r']))
assert_eq(run(lambda: str(made("E", S("r", "raise"), S("e", "raise")))), (('ValueError', 'r'), ['r']))
assert_eq(run(lambda: str(made("D", S("r", "raise"), S("e", "raise")))), (('ValueError', 'r'), ['r']))
assert_eq(run(lambda: str(made("E", S("r", "raise"), Evil("u8")))), (('ValueError', 'r'), ['r']))
assert_eq(run(lambda: str(made("D", S("r", "raise"), Evil("u8")))), (('ValueError', 'r'), ['r']))
assert_eq(run(lambda: str(made("T", S("r", "raise")))), (('ValueError', 'r'), ['r']))
assert_eq(run(lambda: str(made("E", S("r", "int"), "utf-8"))), (('TypeError', 'S.__str__() must return a str, not int'), ['r']))
assert_eq(run(lambda: str(made("D", S("r", "int"), "utf-8"))), (('TypeError', 'S.__str__() must return a str, not int'), ['r']))
assert_eq(run(lambda: str(made("E", S("r", "int"), S("e")))), (('TypeError', 'S.__str__() must return a str, not int'), ['r']))
assert_eq(run(lambda: str(made("D", S("r", "int"), S("e")))), (('TypeError', 'S.__str__() must return a str, not int'), ['r']))
assert_eq(run(lambda: str(made("E", S("r", "int"), S("e", "raise")))), (('TypeError', 'S.__str__() must return a str, not int'), ['r']))
assert_eq(run(lambda: str(made("D", S("r", "int"), S("e", "raise")))), (('TypeError', 'S.__str__() must return a str, not int'), ['r']))
assert_eq(run(lambda: str(made("E", S("r", "int"), Evil("u8")))), (('TypeError', 'S.__str__() must return a str, not int'), ['r']))
assert_eq(run(lambda: str(made("D", S("r", "int"), Evil("u8")))), (('TypeError', 'S.__str__() must return a str, not int'), ['r']))
assert_eq(run(lambda: str(made("T", S("r", "int")))), (('TypeError', 'S.__str__() must return a str, not int'), ['r']))
assert_eq(run(lambda: str(made("E", S("r", "none"), "utf-8"))), (('TypeError', "UnicodeError 'object' attribute must be a string"), ['r']))
assert_eq(run(lambda: str(made("D", S("r", "none"), "utf-8"))), (('TypeError', "UnicodeError 'object' attribute must be a bytes"), ['r']))
assert_eq(run(lambda: str(made("E", S("r", "none"), S("e")))), (('TypeError', "UnicodeError 'object' attribute must be a string"), ['r', 'e']))
assert_eq(run(lambda: str(made("D", S("r", "none"), S("e")))), (('TypeError', "UnicodeError 'object' attribute must be a bytes"), ['r', 'e']))
assert_eq(run(lambda: str(made("E", S("r", "none"), S("e", "raise")))), (('ValueError', 'e'), ['r', 'e']))
assert_eq(run(lambda: str(made("D", S("r", "none"), S("e", "raise")))), (('ValueError', 'e'), ['r', 'e']))
assert_eq(run(lambda: str(made("E", S("r", "none"), Evil("u8")))), (('TypeError', "UnicodeError 'object' attribute must be a string"), ['r', 'evil']))
assert_eq(run(lambda: str(made("D", S("r", "none"), Evil("u8")))), (('TypeError', "UnicodeError 'object' attribute must be a bytes"), ['r', 'evil']))
assert_eq(run(lambda: str(made("T", S("r", "none")))), (('TypeError', "UnicodeError 'object' attribute must be a string"), ['r']))
assert_eq(run(lambda: str(made("E", S("r", "del"), "utf-8"))), (('TypeError', "UnicodeError 'object' attribute is not set"), ['r']))
assert_eq(run(lambda: str(made("D", S("r", "del"), "utf-8"))), (('TypeError', "UnicodeError 'object' attribute is not set"), ['r']))
assert_eq(run(lambda: str(made("E", S("r", "del"), S("e")))), (('TypeError', "UnicodeError 'object' attribute is not set"), ['r', 'e']))
assert_eq(run(lambda: str(made("D", S("r", "del"), S("e")))), (('TypeError', "UnicodeError 'object' attribute is not set"), ['r', 'e']))
assert_eq(run(lambda: str(made("E", S("r", "del"), S("e", "raise")))), (('ValueError', 'e'), ['r', 'e']))
assert_eq(run(lambda: str(made("D", S("r", "del"), S("e", "raise")))), (('ValueError', 'e'), ['r', 'e']))
assert_eq(run(lambda: str(made("E", S("r", "del"), Evil("u8")))), (('TypeError', "UnicodeError 'object' attribute is not set"), ['r', 'evil']))
assert_eq(run(lambda: str(made("D", S("r", "del"), Evil("u8")))), (('TypeError', "UnicodeError 'object' attribute is not set"), ['r', 'evil']))
assert_eq(run(lambda: str(made("T", S("r", "del")))), (('TypeError', "UnicodeError 'object' attribute is not set"), ['r']))
assert_eq(run(lambda: str(made("E", S("r", "enc"), "utf-8"))), ("'<late>' codec can't encode character '\\u20ac' in position 2: <r>", ['r', 'late']))
assert_eq(run(lambda: str(made("D", S("r", "enc"), "utf-8"))), ("'<late>' codec can't decode bytes in position 0-1: <r>", ['r', 'late']))
assert_eq(run(lambda: str(made("E", S("r", "enc"), S("e")))), ("'<late>' codec can't encode character '\\u20ac' in position 2: <r>", ['r', 'late']))
assert_eq(run(lambda: str(made("D", S("r", "enc"), S("e")))), ("'<late>' codec can't decode bytes in position 0-1: <r>", ['r', 'late']))
assert_eq(run(lambda: str(made("E", S("r", "enc"), S("e", "raise")))), ("'<late>' codec can't encode character '\\u20ac' in position 2: <r>", ['r', 'late']))
assert_eq(run(lambda: str(made("D", S("r", "enc"), S("e", "raise")))), ("'<late>' codec can't decode bytes in position 0-1: <r>", ['r', 'late']))
assert_eq(run(lambda: str(made("E", S("r", "enc"), Evil("u8")))), ("'<late>' codec can't encode character '\\u20ac' in position 2: <r>", ['r', 'late']))
assert_eq(run(lambda: str(made("D", S("r", "enc"), Evil("u8")))), ("'<late>' codec can't decode bytes in position 0-1: <r>", ['r', 'late']))
assert_eq(run(lambda: str(made("T", S("r", "enc")))), ("can't translate character '\\x61' in position 0: <r>", ['r']))
assert_eq(run(lambda: str(made("E", Evil("ev"), "utf-8"))), ("'utf-8' codec can't encode character '\\u20ac' in position 2: ev", ['evil']))
assert_eq(run(lambda: str(made("D", Evil("ev"), "utf-8"))), ("'utf-8' codec can't decode bytes in position 0-1: ev", ['evil']))
assert_eq(run(lambda: str(made("E", Evil("ev"), S("e")))), ("'<e>' codec can't encode character '\\u20ac' in position 2: ev", ['evil', 'e']))
assert_eq(run(lambda: str(made("D", Evil("ev"), S("e")))), ("'<e>' codec can't decode bytes in position 0-1: ev", ['evil', 'e']))
assert_eq(run(lambda: str(made("E", Evil("ev"), S("e", "raise")))), (('ValueError', 'e'), ['evil', 'e']))
assert_eq(run(lambda: str(made("D", Evil("ev"), S("e", "raise")))), (('ValueError', 'e'), ['evil', 'e']))
assert_eq(run(lambda: str(made("E", Evil("ev"), Evil("u8")))), ("'u8' codec can't encode character '\\u20ac' in position 2: ev", ['evil', 'evil']))
assert_eq(run(lambda: str(made("D", Evil("ev"), Evil("u8")))), ("'u8' codec can't decode bytes in position 0-1: ev", ['evil', 'evil']))
assert_eq(run(lambda: str(made("T", Evil("ev")))), ("can't translate character '\\x61' in position 0: ev", ['evil']))
assert_eq(run(lambda: str(deleted(made("E", "r", "e"), "reason"))), ("'e' codec can't encode character '\\u20ac' in position 2: <NULL>", []))
assert_eq(run(lambda: str(deleted(made("E", "r", "e"), "encoding"))), ("'<NULL>' codec can't encode character '\\u20ac' in position 2: r", []))
assert_eq(run(lambda: str(deleted(made("D", S("r"), "e"), "object"))), ('', []))
assert_eq(run(lambda: str(UnicodeEncodeError.__new__(UnicodeEncodeError))), ('', []))
assert_eq(run(lambda: deleted(made("E", "r", "e"), "object").object), (None, []))
assert_eq(run(lambda: str(deleted(OSError(2, "x", "f", None, "g"), "filename2"))), ("[Errno 2] x: 'f'", []))
assert_eq(run(lambda: str(deleted(OSError(2, "x", "f"), "filename"))), ('[Errno 2] x', []))
assert_eq(run(lambda: deleted(OSError(2, "x", "f"), "filename").__reduce__()[1:]), (((2, 'x'),), []))
assert_eq(run(lambda: str(deleted(OSError(2, "x"), "errno"))), ("(2, 'x')", []))
assert_eq(run(lambda: repr(deleted(ImportError("m", name="n", path="p"), "name"))), ("ImportError('m', path='p')", []))
assert_eq(run(lambda: deleted(ImportError("m", name="n"), "name").__reduce__()[1:]), ((('m',),), []))
assert_eq(run(lambda: repr(deleted(ImportError("m", name="n"), "name", "name"))), ("ImportError('m')", []))
assert_eq(run(lambda: str(deleted(ImportError("m"), "msg"))), ('m', []))
assert_eq(run(lambda: deleted(AttributeError("x", name="n", obj=1), "name", "obj").__reduce__()[1:]), ((('x',), {'args': ('x',)}), []))
assert_eq(run(lambda: deleted(StopIteration(1), "value").value), (None, []))
assert_eq(run(lambda: deleted(UnicodeEncodeError("x", "a", 0, 1, "z"), "start")), (('TypeError', "can't delete numeric/char attribute"), []))
assert_eq(run(lambda: list(gen())), (["'<gen>' codec can't encode character '\\u20ac' in position 2: <in>"], ['in', 'gen']))
