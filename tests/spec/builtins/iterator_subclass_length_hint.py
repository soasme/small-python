# spec: PLS-315 7.7.7, 27.1
# description: an instance of a subclass of reversed, with no
# __length_hint__ of its own, has reversed's, which asks the sequence's
# __len__ again; called directly too. Its own method wins.
from harness import *
log = []
class Seq:
    def __len__(self): log.append("len"); return 3
    def __getitem__(self, i):
        if i < 3: return i
        raise IndexError
class I(reversed): pass
class J(reversed):
    def __length_hint__(self): log.append("hint"); return 2
assert_eq((list(I(Seq())), log), ([2, 1, 0], ["len", "len"]))
del log[:]
i = I(Seq())
assert_eq((reversed.__length_hint__(i), i.__length_hint__(), log), (3, 3, ["len", "len", "len"]))
del log[:]
assert_eq((list(J(Seq())), log), ([2, 1, 0], ["len", "hint"]))
e = assert_raises(TypeError, reversed.__length_hint__, 1)
assert_eq(str(e), "descriptor '__length_hint__' for 'reversed' objects doesn't apply to a 'int' object")
