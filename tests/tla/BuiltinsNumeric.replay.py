# Replays BuiltinsNumeric.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
class R:
    def __round__(self, n=None): return ("round", n)
    def __abs__(self): return "abs"
class I:
    def __index__(self): return 10
class D:
    def __divmod__(self, other): return "divmod"
    def __rpow__(self, other): return "rpow"
AS = [-25, -15, -7, -1, 0, 3, 8, 25, 35]
BS = [-3, -1, 0, 2, 5]
OPS = ["divmod", "pow", "pow_mod", "pow_mod_by", "round", "abs", "bin", "oct", "hex", "minmax", "sum"]


def numeric(op, a, b):
    try:
        if op == "divmod": return repr(divmod(a, b))
        if op == "pow": return repr(pow(a, b)) if b >= 0 else repr(type(pow(a, b)).__name__)
        if op == "pow_mod": return repr(pow(a, b, 7))
        if op == "pow_mod_by": return repr(pow(a, 2, b))
        if op == "round": return repr(round(a, b))
        if op == "abs": return repr(abs(a))
        if op == "bin": return repr(bin(a))
        if op == "oct": return repr(oct(a))
        if op == "hex": return repr(hex(a))
        if op == "minmax": return repr((min(a, b), max(a, b), min([b, a], key=abs), max((), default=a)))
        if op == "sum": return repr(sum([a, b], 10))
    except (ValueError, ZeroDivisionError) as error:
        return "%s: %s" % (type(error).__name__, error)

SOURCES = {
    "round_half_even": 'result = (round(0.5), round(1.5), round(2.5), round(-0.5), round(-1.5))',
    "round_float_digits": 'result = (round(2.675, 2), round(1234.5, -2), round(0.125, 2), type(round(1.5, 0)).__name__)',
    "round_none": 'result = (round(3.7, None), type(round(3.7, None)).__name__, round(5, None))',
    "round_hook": 'result = (round(R()), round(R(), 2))',
    "round_no_hook": 'result = round(object())',
    "round_inf": "result = round(float('inf'))",
    "round_nan": "result = round(float('nan'))",
    "round_bad_ndigits": 'result = round(1.5, 1.0)',
    "abs_hook": 'result = (abs(R()), abs(-2.5), abs(3 + 4j), abs(True), abs(-0.0))',
    "abs_bad": "result = abs('x')",
    "divmod_float": 'result = (divmod(7.5, 2), divmod(-7.5, 2), divmod(7, -2.0))',
    "divmod_hook": 'result = (divmod(D(), 1), pow(2, D()))',
    "divmod_complex": 'result = divmod(1j, 1)',
    "divmod_zero_float": 'result = divmod(1.0, 0)',
    "pow_float": 'result = (pow(2, 0.5), pow(4, -1), pow(2.0, 3), pow(-8, 1/3).real > 0)',
    "pow_mod_float": 'result = pow(2.0, 3, 5)',
    "pow_keywords": 'result = pow(base=2, exp=10, mod=1000)',
    "pow_zero_zero": 'result = (pow(0, 0), pow(0.0, 0.0), 0 ** 0)',
    "sum_floats": 'result = (sum([0.1] * 10), sum([0.1] * 10) == 1.0, sum([1e100, 1.0, -1e100]))',
    "sum_strings": "result = sum(['a', 'b'], '')",
    "sum_bytes": "result = sum([b'a'], b'')",
    "sum_start_kw": 'result = (sum([1, 2], start=10), sum([[1], [2]], []))',
    "sum_empty": 'result = (sum([]), sum((), 5), type(sum([], 0.0)).__name__)',
    "min_key_default": "result = (min([3, 1, 2], key=lambda x: -x), min([], default='d'), max('abc'), max(1, 2, 3, key=str))",
    "min_empty": 'result = min([])',
    "max_empty": 'result = max(())',
    "min_default_with_many": 'result = min(1, 2, default=0)',
    "min_no_args": 'result = min()',
    "min_first_of_equal": "result = (min([(1, 'a'), (1, 'b')], key=lambda t: t[0]), max([(1, 'a'), (1, 'b')], key=lambda t: t[0]))",
    "max_mixed": "result = max(1, 'a')",
    "bin_index": 'result = (bin(I()), oct(I()), hex(I()), hex(-255))',
    "bin_float": 'result = bin(3.0)',
    "hex_float_method": 'result = (1.5).hex()',
    "complex_forms": "result = (complex(), complex(1), complex(1, 2), complex('1+2j'), complex(' 3j '), complex(1j, 1j))",
    "complex_bad_string": "result = complex('1 + 2j')",
    "complex_string_second": "result = complex('1', 2)",
    "float_forms": "result = (float(), float(' -1.5e3 '), float('-inf'), repr(float('nan')), float('1_0.5'), float(True))",
    "float_bad": "result = float('1__0')",
    "int_forms": "result = (int(), int(3.9), int(-3.9), int('0x1f', 16), int('0x1f', 0), int(' 0b101 ', 0), int('z', 36), int(True))",
    "int_bad_base": "result = int('10', 1)",
    "int_leading_zero": "result = int('010', 0)",
    "int_float_inf": "result = int(float('inf'))",
    "int_float_nan": "result = int(float('nan'))",
    "bool_forms": "result = (bool(), bool(0j), bool([0]), bool(''), bool(' '))",
    "bool_kw": 'result = bool(x=1)'
}


TYPES = {name: value for name, value in list(globals().items()) if isinstance(value, type) and name[0].isupper()}


def generated(p):
    return numeric(p["op"], p["a"], p["b"])


def run(p):
    if "case" not in p:
        return generated(p)
    namespace = dict(TYPES)
    try:
        exec(compile(SOURCES[p["case"]], "<case>", "exec"), namespace)
        return repr(namespace.get("result"))
    except SyntaxError as error:
        return "%s: %s" % (type(error).__name__, error.msg)
    except Exception as error:
        return "%s: %s" % (type(error).__name__, error)


def outcome(p):
    # TLA+ strings are ASCII.
    return run(p).encode("ascii", "backslashreplace").decode()


check_programs(outcome)
