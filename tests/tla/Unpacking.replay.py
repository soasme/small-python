# Replays Unpacking.tla: each case performs the spec's assignment and
# compares what each name was bound to with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def item(kind, k):
    return k if kind == "int" else (k, k + 10) if kind == "pair" else (k, k + 10, k + 20)


def token(value):
    if type(value) is int:
        return "i%d" % value
    return ("t" if len(value) == 2 else "u") + str(value[0])


class Items:
    def __init__(self, items): self.items = items
    def __getitem__(self, i):
        for _ in range(2): pass
        return self.items[i]


def same(x):
    for _ in range(2): pass
    return x


def outcome(p):
    targets, kinds, source = p
    parts, names = [], []
    for i, target in enumerate(targets, 1):
        if target == "name":
            parts.append(f"n{i}"); names.append([f"n{i}"])
        elif target == "star":
            parts.append(f"*s{i}"); names.append([f"s{i}"])
        else:
            parts.append(f"(u{i}, v{i})"); names += [[f"u{i}"], [f"v{i}"]]
    value = tuple(item(kind, k) for k, kind in enumerate(kinds, 1))
    value = value if source == "tuple" else Items(value) if source == "getitem" else map(same, value)
    try:
        code = compile(", ".join(parts) + ", = value", "<program>", "exec")
    except SyntaxError:
        return ("syntax", ())
    namespace = {"value": value}
    try:
        exec(code, namespace)
    except (TypeError, ValueError) as error:
        return (type(error).__name__, ())
    bound = []
    for (name,) in names:
        got = namespace[name]
        bound.append(tuple(token(x) for x in got) if name.startswith("s") else (token(got),))
    return ("ok", tuple(bound))


failures = 0
count = 0
for walk in walks():
    count += 1
    steps = states(walk)
    program = next(steps)["program"]
    for state in steps:
        actual = outcome(program)
        if actual != state["outcome"]:
            failures += 1
            if failures <= 20:
                print("MISMATCH", program, "expected", state["outcome"], "got", actual)
if failures:
    print(failures, "mismatches")
else:
    print("replayed", count, "cases")
