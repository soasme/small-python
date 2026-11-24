# spec: PLS-315 26.4, 26.6, 7.2.4
# description: a dict view's in and dict.__contains__ compare a stored
# key with the probe by the stored key's __eq__ first; its NotImplemented
# calls the probe's reflected __eq__, and neither answering means not
# equal. The result's Python __bool__ or __len__ decides the match.
from harness import *
log = []
class Stored:
    def __hash__(self): return 1
    def __eq__(self, other): log.append("stored"); return NotImplemented
class Probe:
    def __hash__(self): return 1
    def __eq__(self, other): log.append("probe"); return isinstance(other, Stored)
class Neither:
    def __hash__(self): return 1
    def __eq__(self, other): log.append("neither"); return NotImplemented
def run():
    d = {Stored(): "v"}
    return [Probe() in d.keys(), (Probe(), "v") in d.items(), d.__contains__(Probe()), Neither() in d.keys(), d.__contains__(Neither()), log]
assert_eq(run(), [True, True, True, False, False,
                  ["stored", "probe", "stored", "probe", "stored", "probe", "stored", "neither", "stored", "neither"]])
class Truth:
    def __init__(self, t): self.t = t
    def __bool__(self): log.append("bool"); return self.t
class Sized:
    def __len__(self): log.append("len"); return 0
class Answering:
    def __hash__(self): return 1
    def __eq__(self, other): log.append("stored"); return other.answer if isinstance(other, Rich) else NotImplemented
class Rich:
    def __init__(self, answer): self.answer = answer
    def __hash__(self): return 1
    def __eq__(self, other): log.append("rich"); return self.answer
def truths():
    d = {Answering(): "v"}
    return [Rich(Truth(True)) in d.keys(), d.__contains__(Rich(Sized())), (Rich(Truth(False)), "v") in d.items(), log]
log.clear()
assert_eq(truths(), [True, False, False, ["stored", "bool", "stored", "len", "stored", "bool"]])
