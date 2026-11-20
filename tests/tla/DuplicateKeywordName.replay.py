# Replays DuplicateKeywordName.tla: each case calls an instance whose
# __getattribute__ answers __qualname__ and __module__ as the program
# says, with a duplicate keyword, and compares the name in the TypeError
# and the attributes read with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def outcome(p):
    read = []

    class Callee:
        def __getattribute__(self, name):
            # A loop puts the method's body on the machine.
            for _ in ():
                pass
            if name in ("__qualname__", "__module__"):
                read.append(name)
                answer = p["qualname" if name == "__qualname__" else "module"]
                if answer == "absent":
                    raise AttributeError(name)
                if answer == "error":
                    raise LookupError(name)
                return {"str": "Q" if name == "__qualname__" else "mod", "none": None, "builtins": "builtins"}[answer]
            return object.__getattribute__(self, name)

        def __str__(self):
            read.append("__str__")
            return "text" if p["text"] == "str" else 1

        def __call__(self, **kw):
            return kw

    try:
        if p["merge"] == "double":
            Callee()(**{"a": 1}, **{"a": 2})
        else:
            Callee()(**{"a": 1}, a=2)
    except TypeError as e:
        text = str(e)
        suffix = " got multiple values for keyword argument 'a'"
        return (text[:-len(suffix)] if text.endswith(suffix) else text, tuple(read))
    return ("bound", tuple(read))


check_programs(outcome)
