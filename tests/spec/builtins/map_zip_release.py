# spec: PLS-315 9.7, 19.3.3
# description: A map or zip that takes items from a generator keeps no
# reference to an item once it has given it on, so the items it took are
# reclaimed, their __del__ called, when nothing else holds them.
from harness import *

log = []

class Item:
    def __init__(self, i): self.i = i
    def __del__(self): log.append(self.i)

def items(n):
    for i in range(n): yield Item(i)

def run():
    del log[:]
    ids = list(map(id, items(3)))
    for pair in zip(items(3), range(3)): pass
    for n in map(lambda item: item.i, items(2)): pass
    pair = None
    host.collect()
    return sorted(log), len(ids)

expected = ([0, 0, 0, 1, 1, 1, 2, 2], 3)
assert_eq(run(), expected)

def main():
    return run()

assert_eq(main(), expected)
