# spec: PLS-315 23.4, 7.5.5, 7.5.6
# description: str.format of a field with a conversion and a nested spec,
# "{!r:{}}", calls the object's Python __repr__ (or __str__ for !s,
# __repr__ escaped for !a), which may loop, before the nested spec's
# fields are taken, then formats the converted text by that spec, which
# may itself hold a field whose object's Python __format__ is called; by
# position, number or keyword. An exception from the conversion
# propagates before the spec's fields are read. Inside functions as at
# module level.
from harness import *

log = []

class R:
    def __init__(self, tag): self.tag = tag
    def __repr__(self):
        for _ in (): pass
        log.append("repr " + self.tag)
        if self.tag == "bad": raise LookupError("repr")
        return "Ré" + self.tag
    def __str__(self):
        for _ in (): pass
        log.append("str " + self.tag); return "S" + self.tag
    def __format__(self, spec):
        for _ in (): pass
        log.append("format " + self.tag); return spec

class W:
    def __format__(self, spec):
        for _ in (): pass
        log.append("width"); return "8"

def run():
    for _ in (): pass
    return ["{!r:{}}".format(R("a"), ">5"), "{!s:{w}}|{:{}}".format(R("b"), R("c"), "x", w="<4"),
            "{0!a:{1}}".format(R("d"), "^9"), "{!r:>{}}".format(R("e"), W()), "{k!s:{k}}".format(k=R("f")),
            "{!r:{}{}}|{}".format(R("g"), "*", "^7", "end")]

expected = ["  Réa", "Sb  |x", " R\\xe9d  ", "     Rée", "Sf", "**Rég**|end"]
assert_eq(run(), expected)
assert_eq(log, ["repr a", "str b", "format c", "repr d", "repr e", "width", "str f", "format f", "repr g"])
log.clear()

assert_eq("{!r:{}}".format(R("a"), ">5"), expected[0])
assert_eq(log, ["repr a"])
log.clear()

class Spec:
    def __format__(self, spec):
        log.append("spec"); return ""

def errors():
    for _ in (): pass
    try: "{!r:{}}".format(R("bad"), Spec())
    except LookupError as e: return e.args, log

assert_eq(errors(), (("repr",), ["repr bad"]))
