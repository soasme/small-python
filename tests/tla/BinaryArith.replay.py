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
    "bool_slots": "result = (bool.__and__(True, True), bool.__and__(True, 1.0), int.__and__(True, True), "
                  "type(int.__or__(True, False)).__name__, bool.__and__ is int.__and__)",
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
    "pow_overflow": "try:\n    2.0 ** 10000\nexcept OverflowError as e:\n    result = (type(e).__name__, e.args[0], type(e.args[1]).__name__)",
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
    "pow_modulus_method": "log = []\nclass P:\n    def __init__(self, r): self.r = r\n    def __pow__(self, b, m=None):\n        for _ in (): pass\n"
                          "        log.append((b, m))\n        return self.r\n"
                          "def bad():\n    try: pow(P(NotImplemented), 2, 5)\n    except TypeError as e: return str(e)\n"
                          "result = (pow(P(7), 2, 5), log[:], bad())",
    "pow_complex_declines": "class P:\n    def __pow__(self, b, m=None): return NotImplemented\n"
                            "def bad(*a):\n    try: pow(*a)\n    except (TypeError, ValueError) as e: return str(e)\n"
                            "result = (bad(P(), 2, 1j), bad(1j, 2, 3))",
    "seq_mul_overflow": "class Huge:\n    def __index__(self):\n        return 1 << 70\n'a' * Huge()",
    "str_add_int": "'a' + 1",
    "list_add_tuple": "[1] + (2,)",
    "subclass_concat": "class St(str): pass\nclass I(int): pass\ndef f():\n    return St('a') + I(1)\nresult = f()",
    "bytearray_subclass_iconcat": "class BA(bytearray): pass\ndef f():\n    x = BA(b'a')\n    x += 1\nresult = f()",
    "bytes_subclass_concat": "class B(bytes): pass\nclass St(str): pass\ndef f():\n    return B(b'') + St('a')\nresult = f()",
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
    "builtin_declines": "calls = []\nclass R:\n    def __init__(self, a): self.a = a\n    def __ror__(self, o): return self.r(o)\n"
                        "    def __rsub__(self, o): return self.r(o)\n"
                        "    def r(self, o):\n        for _ in (): pass\n        calls.append(1)\n        return ('r', type(o).__name__) if self.a else NotImplemented\n"
                        "class SubList(list): pass\ndef no():\n    s = {1}\n    try: s |= R(0)\n    except TypeError as e: return str(e)\n"
                        "x = SubList()\nx -= R(1)\nresult = ({1} | R(1), x, no(), calls)",
    "divmod_slot_declines": "log = []\nclass R:\n    def __rdivmod__(self, o):\n        for _ in (): pass\n        log.append(o)\n        return ('r', o)\n"
                            "class I(int): pass\nclass F(float): pass\n"
                            "result = (int.__divmod__(7, R()), float.__divmod__(7.5, R()), divmod(I(7), R()), divmod(F(7.5), R()), log)",
    "divmod_descriptor": "log = []\nclass G:\n    def __get__(self, o, t):\n        for _ in (): pass\n        log.append('get')\n"
                         "        def m(other):\n            log.append('m')\n            return ('m', other)\n        return m\n"
                         "class A:\n    __divmod__ = G()\nresult = (divmod(A(), 1), log)",
    "divmod_methods": "log = []\nclass D:\n    def __init__(self, r): self.r = r\n    def __divmod__(self, o):\n        for _ in (): pass\n"
                      "        log.append(('D', self.r))\n        return NotImplemented if self.r == 'ni' else ('D', o)\n"
                      "class E:\n    def __rdivmod__(self, o):\n        for _ in (): pass\n        log.append(('rE', 2))\n        return ('rE', 2)\n"
                      "class S(D):\n    def __rdivmod__(self, o):\n        for _ in (): pass\n        log.append(('rS', 3))\n        return ('rS', 3)\n"
                      "result = (divmod(D(1), 1), divmod(D('ni'), E()), divmod(D(0), S(0)), log)",
    "pow3_float": "pow(1, 2.0, 3)",
    "pow3_complex": "pow(1j, 2, 3)",
    "pow3_zero": "pow(2, 3, 0)",
    "pow3_inverse": "try:\n    pow(2, -1, 4)\nexcept ValueError as e:\n    result = (pow(2, -1, 5), 'ValueError: ' + str(e))",
    "inplace_messages": "class A: pass\na = A()\na <<= 1",
    "inplace_pow_message": "x = 1\nx **= 'a'",
    "sequence_reflected": "class R:\n    def __init__(self, v): self.v = v\n    def __radd__(self, o):\n        for _ in range(2): pass\n        return self.v\n"
                          "    __rmul__ = __radd__\n    def __iter__(self): return iter([7])\n    def __index__(self): return 2\n"
                          "a = [1]; a += R('r')\nb = [1]; c = b; b += R(NotImplemented)\nd = bytearray(b'x'); d *= R(NotImplemented)\n"
                          "result = (a, b, b is c, d)",
    "plain_body_operator": ("log = []\nclass V:\n    def __init__(self, v): self.v = v\n"
                            "    def __add__(self, o):\n        for _ in (): pass\n        log.append('add')\n        return self.v + o\n"
                            "    def __isub__(self, o):\n        for _ in (): pass\n        log.append('isub')\n        return self.v\n"
                            "def plus(x, y): return x + y\ndef sub(x, y):\n    x -= y\n    return x\n"
                            "result = (plus(V(1), 2), sub(V(1), 2), log)"),
    "inplace_subclass_reflected": ("log = []\nclass R:\n"
                                   "    def __rmul__(self, o):\n        for _ in (): pass\n        log.append('rmul')\n        return 'rmul'\n"
                                   "    def __rsub__(self, o):\n        for _ in (): pass\n        log.append('rsub')\n        return 'rsub'\n"
                                   "class L(list): pass\nclass S(set): pass\n"
                                   "x = L([1])\nx *= R()\ny = S({1})\ny -= R()\nresult = (x, y, log)"),
    "repetition_slots": ("def error(f):\n    try:\n        f()\n    except TypeError as e:\n        return str(e)\n"
                         "class S(str):\n    def __mul__(self, o): return NotImplemented\n"
                         "    def __index__(self):\n        for _ in (): pass\n        return 3\n"
                         "class C:\n    def __index__(self): return 2\n"
                         "def augment(x, y):\n    x *= y\n"
                         "x = 2\nx *= 'b'\n"
                         "result = (S('a') * 'b', error(lambda: augment(S('a'), 'b')), error(lambda: augment(C(), 'b')), x)"),
    "complex_declines": ("def error(f):\n    try:\n        f()\n    except TypeError as e:\n        return str(e)\n"
                         "result = (error(lambda: 'b' * 1j), error(lambda: 'b' + 1j), error(lambda: 1j + 'b'))"),
    "inplace_mul_first": ("class R:\n    def __rmul__(self, o): return 'rmul'\n"
                          "class M(list):\n    def __mul__(self, n): return 'mul'\n"
                          "class N(list):\n    def __mul__(self, n): return NotImplemented\n"
                          "x = M([1])\nx *= R()\ny = N([1])\nz = y\ny *= 2\n"
                          "try:\n    z *= 'a'\nexcept TypeError as e:\n    m = str(e)\n"
                          "result = (x, y, y is z, m)"),
    "inplace_inherited": "class SO(set):\n    def __or__(s, o):\n        for _ in (): pass\n        return 'or'\n"
                         "class DO(dict):\n    def __or__(s, o):\n        for _ in (): pass\n        return 'or'\n"
                         "x = SO({1})\nz = x\nx |= {2}\ny = DO(a=1)\nw = y\ny |= {'b': 2}\nresult = (sorted(x), x is z, y, y is w, SO() | {1})",
    "cross_builtin_operand": "log = []\nclass D(dict):\n    def __ror__(s, o):\n        for _ in (): pass\n        log.append('D'); return 'd'\nclass S(set):\n    def __rand__(s, o):\n        for _ in (): pass\n        log.append('S'); return 's'\nclass I(int):\n    def __rxor__(s, o):\n        for _ in (): pass\n        log.append('I'); return 'i'\nresult = ({1} | D(), frozenset() | D(), {'a': 1} & S(), {1} ^ I(2), log)",
    "set_dict_operand": "class S(set):\n    def __ror__(s, o): return 'r'\nclass D(dict):\n    def __ror__(s, o): return 'r'\n"
                        "class Declined(set):\n    def __ror__(s, o): return NotImplemented\nx = frozenset({1})\nx |= S({2})\n"
                        "result = (type(frozenset({1}) | S({2})).__name__, frozendict(a=1) | D(z=9), {1} | S({2}), {'a': 1} | D(z=9), "
                        "sorted({1} | Declined({2})), sorted(x))",
    "sequence_declined": "class R:\n    def __radd__(self, o): return NotImplemented\n    __rmul__ = __radd__\n"
                         "    def __iter__(self):\n        for i in (7, 8): yield i\n    def __length_hint__(self): return 2\n"
                         "    def __index__(self): return 2\nclass Bad(R):\n    def __index__(self): raise KeyError('index')\n"
                         "a = [1]; a *= R()\nb = [1]; c = b; b += R()\ne = bytearray(b'x')\n"
                         "try: e *= Bad()\nexcept KeyError as x: e = repr(x)\nresult = (a, b, b is c, e)",
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
