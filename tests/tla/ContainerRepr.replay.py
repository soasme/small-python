# Replays ContainerRepr.tla: each case builds the program's class and
# container, shows it the program's way, and writes the text, the default
# repr as <C>, and the __repr__ calls as the model does.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

VIA = {"repr": repr, "str": str, "fstring": lambda x: f"{x}", "format": lambda x: "{}".format(x),
       "percent": lambda x: "%s" % (x,), "ascii": ascii, "starred": lambda x: repr(*(x,)), "format_empty": lambda x: format(x, "")}


def outcome(p):
    log = []

    def spin(text):
        for _ in range(2): pass
        log.append(text)
        return text
    def absent(self):
        for _ in range(2): pass
        raise AttributeError("absent")
    body = {"function": {"__repr__": lambda self: spin("c")}, "static": {"__repr__": staticmethod(lambda: spin("s"))},
            "raises": {"__repr__": staticmethod(lambda: spin(1) // 0)},
            "property": {"__repr__": property(lambda self: lambda: spin("p"))}, "absent": {"__repr__": property(absent)}, "none": {}}[p["repr"]]
    C = type("C", (), body)
    c = C()
    shown = {"list": lambda: [c, 1], "tuple": lambda: (c, 1), "dict": lambda: {1: c}, "set": lambda: {c}}[p["container"]]()
    if p["sub"]:
        shown = type("Sub", (type(shown),), {})(shown)
    if p["nested"]:
        shown = [shown]
    try:
        text = VIA[p["via"]](shown)
    except ZeroDivisionError:
        text = "ZeroDivisionError"
    if p["repr"] in ("none", "absent"):
        start = text.index("<")
        text = text[:start] + "<C>" + text[text.index(">", start) + 1:]
    return (text, len(log))

check_programs(outcome)
