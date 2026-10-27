# spec: PLS-315 26.5, 13.2.3, 15.6.4
# description: Any object with keys() and __getitem__ is a mapping for ** and dict(); match needs a built-in mapping.
from harness import *

class Mapping:
    def keys(self):
        return ["a", "b"]
    def __getitem__(self, key):
        return key.upper()
assert_eq({**Mapping()}, {"a": "A", "b": "B"})
assert_eq(dict(Mapping()), {"a": "A", "b": "B"})
assert_eq((lambda **kw: kw)(**Mapping()), {"a": "A", "b": "B"})
d = {}
d.update(Mapping())
assert_eq(d, {"a": "A", "b": "B"})
assert_eq(frozendict(Mapping()), frozendict(a="A", b="B"))

def kind(subject):
    match subject:
        case {"a": _}:
            return "mapping"
        case [*_]:
            return "sequence"
        case _:
            return "other"
assert_eq(kind(Mapping()), "other")
assert_eq(kind({"a": 1}), "mapping")
assert_eq(kind(frozendict(a=1)), "mapping")
assert_eq(kind(type(type.__dict__)({"a": 1})), "mapping")
class DictSub(dict): pass
assert_eq(kind(DictSub(a=1)), "mapping")
class ListSub(list): pass
assert_eq(kind(ListSub([1])), "sequence")
assert_eq(kind("str"), "other")
assert_eq(kind(b"bytes"), "other")
