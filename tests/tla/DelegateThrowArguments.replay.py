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


def outcome(p):
    def gen():
        yield 1
    def chain(inner):
        yield from inner
    first = gen()
    it = first if p["delegate"] == "generator" else chain(first) if p["delegate"] == "chain" else Throws() if p["delegate"] == "throws" else Bare()

    def handling():
        try:
            yield from it
        except Exception as e:
            yield "caught " + type(e).__name__

    def plain():
        yield from it
    g = handling() if p["handles"] else plain()
    next(g)
    args = {"instance": (KeyError("k"),), "invalid": (1,), "exit": (GeneratorExit, 1, 2), "made": (Made, 3), "exit_made": (Exit,), "exit_class": (GeneratorExit,)}[p["args"]]
    closed[:] = [lambda: it.gi_frame is None and first.gi_frame is None if p["delegate"] in ("generator", "chain") else p["delegate"] == "bare" or it.closed]
    try:
        result = repr(g.throw(*args))
    except Exit as e:
        result = "Exit after close" if closed[1] else "Exit before close"
    except GeneratorExit:
        result = "GeneratorExit after close" if closed[0]() else "GeneratorExit before close"
    except Exception as e:
        result = type(e).__name__
    return {"result": result, "suspended": g.gi_frame is not None}


check_programs(outcome)
