# spec: PLS-315 13.16.3, 27.2.2
# description: a yield from of an iterator instance whose class has no
# send, throw or close looks the method up through its Python
# __getattr__ when send(), throw() or close() reaches it: a method it
# returns is called with the value or the exception (none for close), a
# throw's class as given; an AttributeError ends the delegation, a send's
# raising it, a throw's and a close's raising their exception at the
# yield from; a throw's other errors leave the generator suspended, a
# close's are unraisable. Inside functions as at module level.
from harness import *
log = []
class Sub:
    def __iter__(self): return self
    def __next__(self): return 1
    def __getattr__(self, name):
        log.append(name)
        if name == "send": return lambda v: ("sent", v)
        if name == "throw": return self.thrown
        if name == "close": return lambda: log.append("closed")
        raise AttributeError(name)
    def thrown(self, e):
        log.append(e if isinstance(e, type) else type(e))
        return "t"
class Absent:
    def __iter__(self): return self
    def __next__(self): return 1
    def __getattr__(self, name):
        log.append(name)
        raise AttributeError(name)
class Broken(Absent):
    def __getattr__(self, name):
        log.append(name)
        1 / 0
def outer(it):
    try:
        yield from it
    except BaseException as e:
        log.append(("caught", type(e)))
        raise

def check():
    g = outer(Sub()); next(g)
    assert_eq((g.send(5), g.throw(KeyError), g.throw(ValueError()), g.send(None)), (("sent", 5), "t", "t", 1))
    g.close()
    assert_eq(log, ["send", "throw", KeyError, "throw", ValueError, "close", "closed", ("caught", GeneratorExit)])
    log.clear()
    for method, arg, error in (("send", 3, AttributeError), ("throw", KeyError, KeyError)):
        g = outer(Absent()); next(g)
        assert_raises(error, getattr(g, method), arg)
        assert_eq((log, g.gi_frame), ([method, ("caught", error)], None))
        log.clear()
    g = outer(Absent()); next(g)
    assert_eq((g.close(), log, g.gi_frame), (None, ["close", ("caught", GeneratorExit)], None))
    log.clear()
    g = outer(Broken()); next(g)
    assert_raises(ZeroDivisionError, g.throw, KeyError)
    assert_eq((log, g.gi_suspended, next(g)), (["throw"], True, 1))
    log.clear()
    assert_raises(ZeroDivisionError, g.send, 2)
    assert_eq((log, g.gi_frame), (["send", ("caught", ZeroDivisionError)], None))
    log.clear()
    g = outer(Broken()); next(g)
    assert_eq((g.close(), log, g.gi_frame), (None, ["close", ("caught", GeneratorExit)], None))
    log.clear()

check()
def nested():
    check()
nested()
