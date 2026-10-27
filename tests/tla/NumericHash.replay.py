# Replays NumericHash.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

SOURCES = {
    "hash_info": "import sys\nresult = (sys.hash_info.modulus == 2 ** 61 - 1, sys.hash_info.inf, sys.hash_info.imag, sys.hash_info.width)",
    "inf": "result = (hash(float('inf')), hash(float('-inf')))",
    "nan_identity": "x = float('nan')\ny = float('nan')\nresult = (hash(x) == hash(x), hash(x) == object.__hash__(x), hash(x) == hash(y))",
    "modulus": "P = 2 ** 61 - 1\nresult = (hash(P), hash(P + 1), hash(-P), hash(2 * P + 5), hash(P - 1) == P - 1)",
    "minus_one": "result = (hash(-1), hash(-1.0), hash(complex(-1, 0)), hash(-1) == hash(-2))",
    "bool": "result = (hash(True), hash(False), hash(True) == hash(1.0))",
    "complex_real": "result = all(hash(complex(x, 0)) == hash(x) for x in (0.5, -3.0, 7, 1e300))",
    "complex_formula": "import sys\nz = complex(0.5, -2.25)\nM = 2 ** 63\nh = hash(0.5) + sys.hash_info.imag * hash(-2.25)\nh = (h & (M - 1)) - (h & M)\nresult = hash(z) == (-2 if h == -1 else h)",
    "complex_imag_only": "result = hash(1j) == 1000003",
    "complex_inf": "result = hash(complex(float('inf'), 1)) == 314159 + 1000003",
    "equal_implies_hash": "xs = [0, 0.0, -0.0, 0j, False, 1, 1.0, True, 2 ** 70, float(2 ** 70), 0.5, complex(0.5)]\nresult = all(hash(a) == hash(b) for a in xs for b in xs if a == b)",
    "negative_zero": "result = (hash(-0.0), hash(0.0))",
    "dict_key_equal_numbers": "d = {1: 'int'}\nd[1.0] = 'float'\nd[True] = 'bool'\nresult = d",
    "set_mixed": "result = len({1, 1.0, True, 1 + 0j})",
    "int_subclass": "class N(int): pass\nresult = hash(N(5)) == 5",
    "float_subclass": "class G(float): pass\nresult = hash(G(0.5)) == hash(0.5)",
    "hash_returns_int": "result = type(hash(1.5)).__name__",
    "big_negative": "result = hash(-(2 ** 64)) == -8",
    "large_float_integral": "result = hash(1e300) == hash(int(1e300))"
}


P = 2 ** 61 - 1


def canonical(h):
    """0, or rot(o, j) with o odd and below 2 ** 24 rotated left by j bits
    within 61 bits giving abs(h), negated with a leading minus."""
    if h == 0:
        return "0"
    sign, h = ("-", -h) if h < 0 else ("", h)
    for j in range(61):
        o = ((h >> j) | (h << (61 - j))) & P
        if o % 2 and o < 2 ** 24:
            return "%srot(%d, %d)" % (sign, o, j)
    return "unrotatable %d" % h


def generated(p):
    if p["type"] == "int":
        x = p["m"] * 2 ** p["e"]
    else:
        x = float(p["m"]) * 2.0 ** p["e"]
    return canonical(hash(-x if p["negative"] else x))


def outcome(p):
    if "case" not in p:
        return generated(p)
    namespace = {}
    try:
        exec(compile(SOURCES[p["case"]], "<case>", "exec"), namespace)
        return repr(namespace.get("result"))
    except SyntaxError as error:
        return "%s: %s" % (type(error).__name__, error.msg)
    except Exception as error:
        return "%s: %s" % (type(error).__name__, error)


check_programs(outcome)
