# spec: PLS-315 24.1.1, 7.7.6
# description: list.__init__, bound or given the list, empties the list,
# then extends it in place from the iterable: its __iter__, which may loop,
# and length hint, and a generator's body, see the list empty, then
# growing; an error leaves the list empty. No argument leaves it empty,
# and a keyword or a second argument is refused. Lists and list
# subclasses, inside functions as at module level.
from harness import *

log = []
class It:
    def __init__(self, target, items): self.target, self.items = target, items
    def __iter__(self):
        for _ in (): pass
        log.append(("iter", list(self.target)))
        return iter(self.items)
    def __len__(self):
        for _ in (): pass
        log.append(("len", list(self.target))); return 1
def gen(target):
    for i in range(2):
        log.append(("gen", list(target)))
        yield i
class L(list): pass
def inits():
    del log[:]
    out = []
    l = [9]; out.append((l.__init__(It(l, [1, 2])), l))
    l = [9]; out.append((l.__init__(gen(l)), l))
    m = L([5]); out.append((m.__init__(It(m, [3])), m, type(m).__name__))
    l = [9]; list.__init__(l, It(l, [4])); out.append(l)
    out.append(list.__init__([], It([], [1])))
    m = L([5]); list.__init__(m, gen(m)); out.append(m)
    l = [9, 8]; l.__init__(l); out.append(l)
    l = [9]; l.__init__(); out.append(l)
    for call in (lambda: l.__init__(x=1), lambda: l.__init__(1, 2), lambda: l.__init__(5)):
        try: call()
        except TypeError as e: out.append(str(e))
    class R:
        def __iter__(self):
            for _ in (): pass
            raise KeyError("k")
    l = [9]
    try: l.__init__(R())
    except KeyError: out.append(l)
    return out, log

expected = ([(None, [1, 2]), (None, [0, 1]), (None, [3], 'L'), [4], None, [0, 1], [], [], 'list() takes no keyword arguments', 'list expected at most 1 argument, got 2', "'int' object is not iterable", []], [('iter', []), ('len', []), ('gen', []), ('gen', [0]), ('iter', []), ('len', []), ('iter', []), ('len', []), ('iter', []), ('len', []), ('gen', []), ('gen', [0])])
assert_eq(inits(), expected)

def nested():
    return inits()

assert_eq(nested(), expected)
