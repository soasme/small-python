# spec: PLS-315 10.4.2
# description: a class's __text_signature__, a read-only data descriptor
# on type, is the parenthesized text that the doc it was made with gives
# after the last dotted part of its current name, through the first ")"
# that "\n--\n\n" follows, unless a blank line comes first; otherwise
# None. Reassigning __doc__ does not change it, a class attribute of the
# name does not hide it, and a subclass does not inherit it.
from harness import assert_eq, assert_raises

class E:
    "E(a, b)\n--\n\nDoc."
class Plain: pass
class Own: __text_signature__ = "x"
class Sub(E): pass
class S(str): pass

assert_eq([E.__text_signature__, Plain.__text_signature__, Own.__text_signature__, Own().__text_signature__,
           Sub.__text_signature__], ["(a, b)", None, None, "x", None])
E.__doc__ = "E(c)\n--\n\n"
assert_eq(E.__text_signature__, "(a, b)")
E.__name__ = "F"
assert_eq(E.__text_signature__, None)
E.__name__ = "E"
late = type("L", (), {})
late.__doc__ = "L(c)\n--\n\n"
assert_eq(late.__text_signature__, None)

made = [type(name, (), {"__doc__": doc}).__text_signature__ for name, doc in [
    ("p.A", "A(x)\n--\n\n"), ("p.B", "p.B(x)\n--\n\n"), ("C", S("C(y)\n--\n\n")), ("D", "D(a)\n\n--\n\n"),
    ("G", "G(a) x)\n--\n\n"), ("H", "H()\n--\n\n"), ("I", "I(a)\n--\n"), ("J", "Jx(a)\n--\n\n"), ("K", 5)]]
assert_eq(made, ["(x)", None, "(y)", None, "(a) x)", "()", None, None, None])

assert_eq(type(type.__dict__["__text_signature__"]).__name__, "getset_descriptor")
assert_eq(type.__dict__["__text_signature__"].__get__(E), "(a, b)")
for act in (lambda: setattr(E, "__text_signature__", "(z)"), lambda: delattr(E, "__text_signature__")):
    assert_eq(str(assert_raises(AttributeError, act)), "attribute '__text_signature__' of 'type' objects is not writable")

class Meta(type):
    @property
    def __text_signature__(cls): return "meta"
class M(metaclass=Meta):
    "M(q)\n--\n\n"
assert_eq(M.__text_signature__, "meta")
