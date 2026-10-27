# Replays BinaryArith.tla: each case builds the spec's classes A and B and
# applies the spec's operator to their instances (or runs one of the spec's
# sources), logging the arithmetic methods called, and compares the result
# and the log with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

NAMES = ("add", "sub", "mul", "matmul", "pow", "lshift")
SOURCES = {
    "int_float": "result = (1 + 1.0, type(1 + 1.0).__name__, 3 * 0.5)",
    "true_div": "result = (7 / 2, 4 / 2, type(4 / 2).__name__)",
    "floor_div": "result = (7 // 2, -7 // 2, 7 // -2, 7.0 // 2, -7.5 // 2)",
    "mod_sign": "result = (7 % 3, -7 % 3, 7 % -3, -7.5 % 2, 7.5 % -2, -0.0 % 1)",
    "divmod": "result = (divmod(-7, 2), divmod(7.5, -2))",
    "complex_mix": "result = (1 + 2j, 1.5 * 2j, (1 + 2j) * (3 - 1j), type(1j + 1).__name__)",
    "complex_floordiv": "1j // 2",
    "complex_mod": "1j % 2",
    "bool_arith": "result = (True + True, True * 3.5, -True, ~False, True / 2, type(True + 0).__name__)",
    "int_div_zero": "1 / 0",
    "int_floordiv_zero": "1 // 0",
    "int_mod_zero": "1 % 0",
    "float_div_zero": "1.0 / 0",
    "float_mod_zero": "1.0 % 0",
    "complex_div_zero": "1j / 0",
    "pow_neg": "result = (2 ** -1, type(2 ** -1).__name__, 2 ** 0, 0 ** 0)",
    "pow_frac_neg": "result = type((-8) ** (1 / 3)).__name__",
    "pow_zero_neg": "0 ** -1",
    "pow_zero_neg_float": "0.0 ** -1",
    "pow_precedence": "result = (-2 ** 2, 2 ** -1, 2 ** 3 ** 2, (-2) ** 2)",
    "pow_overflow": "2.0 ** 10000",
    "pow_float_neg_frac": "result = (-8.0) ** 0.5",
    "int_to_float_overflow": "10 ** 400 * 1.0",
    "int_true_div_big": "result = 10 ** 400 / 10 ** 399",
    "int_true_div_overflow": "10 ** 400 / 3",
    "unary_str": "+'a'",
    "unary_neg_list": "-[]",
    "unary_invert_float": "~1.5",
    "unary_ops": "result = (-(-3), +3.5, ~5, -0.0, abs(-2))",
    "str_mul": "result = ('ab' * 2, 2 * 'ab', [0] * 3, 'a' * -1, 'a' * True)",
    "str_mul_float": "'a' * 2.0",
    "str_add_int": "'a' + 1",
    "list_add_tuple": "[1] + (2,)",
    "int_add_str": "1 + 'a'",
    "matmul_int": "1 @ 2",
    "float_floor_big": "result = (1e300 // 1e-300 == float('inf'), 5.0 // 0.1)",
    "nan_inf": "result = (float('inf') - float('inf'), float('inf') * 0, 1 / float('inf'))",
    "shift_neg": "1 << -1",
    "shift_float": "1 << 1.0",
    "bitwise_float": "1 & 1.0",
    "big_mul": "result = (2 ** 64 * 2 ** 64, -(2 ** 63) // -1, (2 ** 63) % 7)",
    "round_half_even": "result = (7 // 2 * 2 + 7 % 2, round(2.5), round(-0.5))",
    "complex_zero_power": "0j ** -1",
    "complex_overflow": "(1 + 1j) ** 1000000",
    "complex_matmul": "1j @ 1j",
    "bool_matmul": "True @ False",
    "complex_shift": "1j << 1",
    "divmod_complex": "divmod(1j, 1)",
    "complex_zero_div": "complex(1, 2) / 0j",
    "pow3_instance": "class A: pass\npow(A(), 1, 2)",
    "pow3_methods": "class P:\n    def __pow__(self, o, m=None): return ('P', o, m)\n"
                    "    def __rpow__(self, o, m=None): return ('rP', o, m)\nresult = (pow(P(), 2, 3), pow(2, P(), 3))",
    "pow3_float": "pow(1, 2.0, 3)",
    "pow3_complex": "pow(1j, 2, 3)",
    "pow3_zero": "pow(2, 3, 0)",
    "pow3_inverse": "try:\n    pow(2, -1, 4)\nexcept ValueError as e:\n    result = (pow(2, -1, 5), 'ValueError: ' + str(e))",
    "inplace_messages": "class A: pass\na = A()\na <<= 1",
    "inplace_pow_message": "x = 1\nx **= 'a'",
}


def build(kind, name, base, log):
    def method(m, decline):
        def operate(self, other):
            entry = "%s.%s(%s)" % (name, m, self.side)
            log.append(entry)
            return NotImplemented if decline else entry
        return operate

    prefixes = {"value": ("", "r"), "notimpl": ("", "r"), "rop_only": ("r",), "iop": ("i",)}.get(kind, ())
    methods = {}
    for n in NAMES:
        for prefix in prefixes:
            m = "__%s%s__" % (prefix, n)
            methods[m] = method(m, kind == "notimpl")
    return type(name, (base,), methods)


def outcome(p):
    namespace = {}
    if "case" in p:
        try:
            exec(compile(SOURCES[p["case"]], "<case>", "exec"), namespace)
            result = repr(namespace.get("result"))
        except Exception as error:
            result = "%s: %s" % (type(error).__name__, error)
        return (result, ())
    log = []
    A = build(p["left"], "A", object, log)
    B = A if p["relation"] == "same" else build(p["right"], "B", A if p["relation"] == "sub" else object, log)
    a, b = A(), B()
    a.side, b.side = "L", "R"
    namespace = {"a": a, "b": b}
    try:
        if p["op"].endswith("="):
            exec("a %s b" % p["op"], namespace)
            result = "<self>" if namespace["a"] is a else repr(namespace["a"])
        else:
            result = repr(eval("a %s b" % p["op"], namespace))
    except TypeError as error:
        result = "TypeError: %s" % error
    return (result, tuple(log))


check_programs(outcome)
