# Replays Buffers.tla: each case exports a buffer from the spec's class B
# and compares the log of __buffer__ and __release_buffer__ calls and the
# result with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def export(p, log):
    def __buffer__(self, flags):
        log.append("buffer")
        return memoryview(b"abc") if p["ret"] == "view" else b"abc"
    body = {"__buffer__": __buffer__}
    if p["release"]:
        body["__release_buffer__"] = lambda self, view: log.append("release")
    B = type("B", (), body)
    how = p["how"]
    if how == "bytes":
        return repr(bytes(B()))
    m = memoryview(B())
    if how == "with":
        with m:
            data = bytes(m)
    elif how == "release":
        data = bytes(m)
        m.release()
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


def outcome(p):
    log = []
    try:
        if p["part"] == "export":
            result = export(p, log)
        elif p["part"] == "resize":
            result = resize(p)
        else:
            result = repr(memoryview(object()))
    except (TypeError, BufferError) as error:
        result = type(error).__name__
    return " ".join(log + [result])


check_programs(outcome)
