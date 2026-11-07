# spec: PLS-315 25.1.4, 19.3.34
# description: sorted() and list.sort() of instances whose __lt__ loops,
# inside functions as at module level: a stable sort, reversed stably,
# making the same comparisons; a declined __lt__ falls back to the other
# operand's __gt__; a raising comparison propagates with every item still
# in the list; a list changed while it sorts raises ValueError.
from harness import *

class Item:
    compared = 0
    def __init__(self, key, tag): self.key, self.tag = key, tag
    def __lt__(self, other):
        for _ in range(2): pass
        Item.compared += 1
        return self.key < other.key
    def __repr__(self): return f"{self.key}{self.tag}"

def items():
    seed, out = 7, []
    for i in range(40):
        seed = (seed * 1103515245 + 12345) % 2147483648
        out.append(Item(seed % 5, i))
    return out

def counted(sort):
    Item.compared = 0
    result = [repr(x) for x in sort()]
    return result, Item.compared

def sorts():
    data = items()
    tagged = sorted(data, key=lambda x: (x.key, x.tag))
    out = [counted(lambda: sorted(data)), counted(lambda: sorted(tuple(data), reverse=True))]
    copy = data[:]
    copy.sort(reverse=True)
    out.append([repr(x) for x in copy])
    out.append([repr(x) for x in tagged] == out[0][0])
    return out

inside = sorts()
outside = [counted(lambda: sorted(items())), counted(lambda: sorted(tuple(items()), reverse=True))]
assert_eq(inside[:2], outside)
# Called from native code (map), the sort makes the same comparisons.
assert_eq(counted(lambda: next(map(sorted, [items()]))), outside[0])
assert_eq(inside[2], inside[1][0])
assert inside[3]
reverse_keys = [x[0] for x in inside[1][0]]
assert_eq(reverse_keys, sorted(reverse_keys, reverse=True))
# Equal keys keep their order when reversed too.
assert_eq([x for x in inside[1][0] if x[0] == "0"], [x for x in inside[0][0] if x[0] == "0"])

class Number:
    def __init__(self, n): self.n = n
    def __lt__(self, other): return self.n < (other.n if isinstance(other, Number) else other)
    def __gt__(self, other):
        if isinstance(other, str): raise TypeError("no strings")
        return self.n > other

class Declining:
    def __init__(self, n): self.n = n
    def __lt__(self, other): return NotImplemented
    def __gt__(self, other): return self.n > other.n

class Raising:
    def __init__(self, n): self.n = n
    def __lt__(self, other):
        if self.n == 3: raise KeyError(self.n)
        return self.n < other.n

class Growing:
    def __init__(self, n, into): self.n, self.into = n, into
    def __lt__(self, other):
        self.into.append(0)
        return self.n < other.n

def failures():
    out = [[d.n for d in sorted([Declining(2), Declining(1), Declining(3)])]]
    # An int compared first leaves its own __lt__ for the reflected __gt__.
    out.append([getattr(x, "n", x) for x in sorted([Number(2), Number(1), 0, 3])])
    try:
        sorted([Number(2), Number(1), "a"])
    except TypeError as e:
        out.append(str(e))
    data = [Raising(n) for n in (2, 1, 4, 3, 0)]
    try:
        data.sort()
    except KeyError as e:
        out.append((e.args, sorted(x.n for x in data)))
    target = []
    target.extend(Growing(n, target) for n in (2, 1))
    try:
        target.sort()
    except ValueError as e:
        out.append((str(e), [x.n for x in target[:2]]))
    return out

assert_eq(failures(), [[1, 2, 3], [0, 1, 2, 3], "no strings", ((3,), [0, 1, 2, 3, 4]), ("list modified during sort", [1, 2])])
