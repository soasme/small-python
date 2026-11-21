# Replays DelegateThrowArguments.tla: each case throws into a generator
# suspended in a yield from of the spec's delegate, and compares the
# throw()'s result and whether the generator is still suspended.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


class Throws:
    closed = False
    def __iter__(self): return self
    def __next__(self): return 1
    def throw(self, *args): return "thrown"
    def close(self): self.closed = True


class Made(Exception):
    def __init__(self, *args):
        for _ in ():  # a loop: the method runs on the machine
            pass
        super().__init__(*args)


class Swapped(Exception):
    def __new__(cls, *args):
        for _ in ():
            pass
        return Made(*args) if not isinstance(args[0], Made) else super().__new__(cls, *args)


closed = []


class Exit(GeneratorExit):
    def __init__(self, *args):
        for _ in ():
            pass
        closed.append(closed[0]())
        super().__init__(*args)


class Bare:
    def __iter__(self): return self
    def __next__(self): return 1


class Failing(Throws):
    def close(self): raise ValueError


def stubborn():
    try:
        yield 1
    except GeneratorExit:
        yield 2


class Asked(Bare):
    def __init__(self): self.inner = Throws()
    def __getattr__(self, name): return getattr(self.inner, name)


class Broken(Bare):
    def __getattr__(self, name): 1 / 0


def outcome(p):
    def gen():
        yield 1
    def chain(inner):
        yield from inner
    first = gen()
    it = first if p["delegate"] in ("generator", "ended") else chain(first) if p["delegate"] == "chain" else \
        {"throws": Throws, "asked": Asked, "broken": Broken, "bare": Bare, "stubborn": stubborn, "failing": Failing}[p["delegate"]]()

    def handling():
        try:
            yield from it
        except Exception as e:
            yield "caught " + type(e).__name__

    def plain():
        yield from it
    g = handling() if p["handles"] else plain()
    next(g)
    if p["delegate"] == "ended":
        first.close()
    args = {"instance": (KeyError("k"),), "invalid": (1,), "exit": (GeneratorExit, 1, 2), "made": (Made, 3), "swapped": (Swapped, 3), "exit_made": (Exit,), "exit_value": (Exit, (4, 5)), "exit_class": (GeneratorExit,),
            "instance_value": (KeyError("k"), 1), "traceback": (KeyError, None, 2)}[p["args"]]
    closed[:] = [lambda: it.gi_frame is None and first.gi_frame is None if p["delegate"] in ("generator", "chain", "ended") else p["delegate"] in ("bare", "broken") or (it.inner if p["delegate"] == "asked" else it).closed]
    try:
        result = repr(g.throw(*args))
    except Exit as e:
        result = ("Exit %r" % (e.args,) if e.args else "Exit") + (" after close" if closed[1] else " before close")
    except GeneratorExit:
        result = "GeneratorExit after close" if closed[0]() else "GeneratorExit before close"
    except Exception as e:
        result = type(e).__name__
    return {"result": result, "suspended": g.gi_frame is not None}


check_programs(outcome)
