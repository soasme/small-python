# spec: PLS-315 15.5.2
# description: An async with whose manager's __aenter__ and __aexit__ are
# plain Python functions calls each, which may loop, and awaits what it
# returns: __aenter__'s awaited value is the target's, __aexit__ gets the
# body's exception, its awaited true value suppressing it; an exception
# from either call propagates, __aexit__'s with the body's as context,
# and a result that is not awaitable raises TypeError. Inside functions
# as at module level.
from harness import *

log = []

class Ready:
    def __init__(self, value): self.value = value
    def __await__(self):
        log.append(("await", self.value))
        yield "paused"
        return self.value

class Manager:
    def __init__(self, swallow=False, bad=None): self.swallow, self.bad = swallow, bad
    def __aenter__(self):
        for _ in range(2): pass
        log.append("enter")
        if self.bad == "enter": raise LookupError("enter")
        return Ready("managed")
    def __aexit__(self, kind, value, traceback):
        for _ in range(2): pass
        log.append(("exit", kind.__name__ if kind else None))
        if self.bad == "exit": raise LookupError("exit")
        if self.bad == "value": return 1
        return Ready(self.swallow)

async def attempt(manager, raises):
    async with manager as v:
        log.append(v)
        if raises: raise KeyError("body")
    return "done"

def drive(manager, raises=False):
    c = attempt(manager, raises)
    try:
        while True: c.send(None)
    except StopIteration as e:
        return e.value
    except Exception as e:
        return type(e).__name__, str(e), type(e.__context__).__name__

def results():
    del log[:]
    out = [drive(Manager()), drive(Manager(True), True), drive(Manager(), True), drive(Manager(bad="enter")),
           drive(Manager(bad="exit"), True), drive(Manager(bad="value"))]
    return out + [list(log)]

expected = ['done', 'done', ('KeyError', "'body'", 'NoneType'), ('LookupError', 'enter', 'NoneType'),
            ('LookupError', 'exit', 'KeyError'),
            ('TypeError', "'async with' received an object from __aexit__ that does not implement __await__: int",
             'NoneType'),
            ['enter', ('await', 'managed'), 'managed', ('exit', None), ('await', False), 'enter', ('await', 'managed'),
             'managed', ('exit', 'KeyError'), ('await', True), 'enter', ('await', 'managed'), 'managed',
             ('exit', 'KeyError'), ('await', False), 'enter', 'enter', ('await', 'managed'), 'managed',
             ('exit', 'KeyError'), 'enter', ('await', 'managed'), 'managed', ('exit', None)]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
