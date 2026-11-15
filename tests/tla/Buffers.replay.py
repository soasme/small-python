# Replays Buffers.tla: each case exports a buffer from the spec's class B
# and compares the log of __buffer__ and __release_buffer__ calls and the
# result with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def export(p, log):
    def __buffer__(self, flags):
        log.extend(["buffer", str(flags)])
        if p["ret"] == "raise":
            raise ValueError
        return memoryview(b"abc") if p["ret"] == "view" else b"abc"
    body = {"__buffer__": __buffer__}
    if p["release"]:
        body["__release_buffer__"] = lambda self, view: log.append("release")
    B = type("B", (), body)
    how = p["how"]
    if how == "bytes":
        return repr(bytes(B()))
    if how == "bytearray":
        return repr(bytes(bytearray(B())))
    m = memoryview(B())
    if how == "with":
        with m:
            data = bytes(m)
    elif how == "release":
        data = bytes(m)
        m.release()
    elif how == "unbound":
        data = bytes(m)
        memoryview.release(m)
    else:
        data = bytes(m)
        del m
    return repr(data)


def resize(p):
    ba = bytearray(b"ab")
    m = memoryview(ba)
    if p["released"]:
        m.release()
    ba.append(1)
    return repr(len(ba))


def reenter(p):
    during = p["during"]

    def release():
        m.release()
        ba.clear()

    class Exporter(bytearray):
        def __hash__(self):
            release()
            return 1

    class Index:
        def __index__(self):
            release()
            return 0

    class Sep(bytes):
        def __len__(self):
            release()
            return 1

    ba = Exporter(b"ab") if during == "hash" else bytearray(b"ab")
    m = memoryview(ba).toreadonly() if during == "hash" else memoryview(ba)
    if during == "index":
        return repr(m[Index()])
    if during == "store":
        m[0] = Index()
        return repr(bytes(ba))
    if during == "hash":
        return repr(hash(m))
    return m.hex(Sep(b":"))


class Key:
    def __init__(self, log): self.log = log
    def __index__(self):
        for _ in (): pass
        self.log.append("index")
        return 1


def index(p, log):
    m = memoryview(bytearray(b"ab"))
    view = p["view"]
    if view == "released": m.release()
    elif view == "readonly": m = m.toreadonly()
    elif view == "zero": m = memoryview(bytearray(b"a")).cast("B", ())
    elif view == "grid": m = m.cast("B", (1, 2))
    if not p["store"]:
        return repr(m[Key(log)])
    m[Key(log)] = 66
    return repr(bytes(m.obj))


class Logged:
    def __init__(self, log, name, value): self.log, self.name, self.value = log, name, value
    def __index__(self):
        for _ in (): pass
        self.log.append(self.name)
        return self.value


def grid(p, log):
    m = memoryview(bytearray(b"abcd")).cast("B", (2, 2))
    key = (Logged(log, "a", 0 if p["first"] == "in" else 5), Logged(log, "b", 1))
    if not p["store"]:
        return repr(m[key])
    m[key] = 66
    return repr(bytes(m.obj))


def outcome(p):
    log = []
    try:
        if p["part"] == "export":
            result = export(p, log)
        elif p["part"] == "resize":
            result = resize(p)
        elif p["part"] == "reenter":
            result = reenter(p)
        elif p["part"] == "index":
            result = index(p, log)
        elif p["part"] == "grid":
            result = grid(p, log)
        else:
            result = repr(memoryview(object()))
    except (TypeError, BufferError, ValueError, NotImplementedError, IndexError) as error:
        result = type(error).__name__
    return " ".join(log + [result])


check_programs(outcome)
