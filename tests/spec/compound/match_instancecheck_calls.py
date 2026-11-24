# spec: PLS-315 15.6.5, 7.10.2
# description: A class pattern tests its subject by isinstance(), calling
# the class's metaclass's Python __instancecheck__, which may loop, unless
# the subject's class is the class itself; the result's truth, by a
# Python __bool__ too, decides the match; an exception from either
# propagates out of the match.
from harness import *

log = []
class Truth:
    def __init__(self, value): self.value = value
    def __bool__(self):
        for _ in range(2): pass
        log.append(("bool", self.value))
        if self.value is None: raise ValueError("bool")
        return self.value
class Meta(type):
    def __instancecheck__(cls, instance):
        for _ in range(2): pass
        log.append(("check", cls.__name__, instance))
        if instance == "raise": raise LookupError("check")
        return Truth(None if instance == "bad" else instance != 0)
class P(metaclass=Meta): pass
def kind(subject):
    del log[:]
    try:
        match subject:
            case P(): r = "P"
            case _: r = "other"
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def inside():
    return [kind(5), kind(0), kind("raise"), kind("bad"), kind(P())]
expected = [("P", [("check", "P", 5), ("bool", True)]), ("other", [("check", "P", 0), ("bool", False)]),
            (("LookupError", "check"), [("check", "P", "raise")]),
            (("ValueError", "bool"), [("check", "P", "bad"), ("bool", None)]), ("P", [])]
assert_eq(inside(), expected)
assert_eq([kind(5), kind(0), kind("raise"), kind("bad"), kind(P())], expected)
