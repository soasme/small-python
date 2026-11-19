# spec: PLS-315 15.5.1, 7.9.1, 7.3.2, 7.2.4
# description: A with statement reads __exit__, then __enter__, from the
# manager's type, through a descriptor's __get__ or a property's getter
# when the class holds one, then calls what __enter__ read; a read's error
# propagates and a missing method raises TypeError. On an exception,
# __exit__'s result is tested by its own __bool__ or __len__: a true one
# suppresses it, an error there replaces it with the original as its
# context. The calls may loop and pause inside a generator.
from harness import *

log = []
class Reads:
    def __init__(self, name): self.name = name
    def __get__(self, obj, owner):
        for _ in range(2): pass
        log.append("get " + self.name)
        if self.name == "enter":
            def enter():
                for _ in range(2): pass
                log.append("enter")
                return 7
            return enter
        def exit(kind, value, traceback):
            log.append("exit " + (kind.__name__ if kind else "None"))
            return self.name == "suppress"
        return exit
class M:
    __enter__ = Reads("enter")
    __exit__ = Reads("exit")
class Suppress:
    __enter__ = Reads("enter")
    __exit__ = Reads("suppress")
class Prop:
    @property
    def __enter__(self):
        log.append("prop enter")
        return lambda: "p"
    def __exit__(self, *args): log.append("prop exit")
class NoEnter:
    __exit__ = Reads("exit")
class FailExit:
    @property
    def __exit__(self): raise LookupError("exit read")
    def __enter__(self): log.append("never")
class FailEnter:
    def __exit__(self, *args): log.append("never")
    @property
    def __enter__(self): raise LookupError("enter read")

class Truth:
    def __init__(self, value): self.value = value
    def __bool__(self):
        for _ in range(2): pass
        log.append("bool")
        return self.value
class Empty:
    def __len__(self): log.append("len"); return 0
class WrongBool:
    def __bool__(self): return 1
class RaisingBool:
    def __bool__(self): raise LookupError("bool")
class Gives:
    def __init__(self, result): self.result = result
    def __enter__(self): return self
    def __exit__(self, *args): log.append("exit"); return self.result

def failed(e): return "%s: %s (context %s)" % (type(e).__name__, e, type(e.__context__).__name__)

def reads():
    with M() as v: log.append(v)
    with Suppress(): raise KeyError
    with Prop() as p: log.append(p)
    for cls in (NoEnter, FailExit, FailEnter):
        try:
            with cls(): log.append("body")
        except Exception as e: log.append(failed(e))
    try:
        with M(): 1 / 0
    except ZeroDivisionError: log.append("propagated")
    return log[:]

def truths():
    del log[:]
    for result in (Truth(True), Truth(False), Empty(), WrongBool(), RaisingBool()):
        try:
            with Gives(result): raise KeyError("k")
            log.append("suppressed")
        except Exception as e: log.append(failed(e))
    with Gives(Truth(True)): log.append("no exception")
    return log[:]

READS = ["get exit", "get enter", "enter", 7, "exit None", "get suppress", "get enter", "enter", "exit KeyError",
         "prop enter", "p", "prop exit", "get exit",
         "TypeError: 'NoEnter' object does not support the context manager protocol (missed __enter__ method) (context NoneType)",
         "LookupError: exit read (context NoneType)", "LookupError: enter read (context NoneType)",
         "get exit", "get enter", "enter", "exit ZeroDivisionError", "propagated"]
TRUTHS = ["exit", "bool", "suppressed", "exit", "bool", "KeyError: 'k' (context NoneType)",
          "exit", "len", "KeyError: 'k' (context NoneType)",
          "exit", "TypeError: WrongBool.__bool__() must return a bool, not int (context KeyError)",
          "exit", "LookupError: bool (context KeyError)", "no exception", "exit"]

def paused():
    def gen():
        with M() as v:
            yield v
        with Gives(Truth(True)):
            yield "inside"
            raise KeyError
        yield "after"
    del log[:]
    return list(gen()), log[:]

PAUSED = ([7, "inside", "after"], ["get exit", "get enter", "enter", "exit None", "exit", "bool"])

def main():
    del log[:]
    return reads(), truths(), paused()

assert_eq(main(), (READS, TRUTHS, PAUSED))
del log[:]
assert_eq((reads(), truths(), paused()), (READS, TRUTHS, PAUSED))
