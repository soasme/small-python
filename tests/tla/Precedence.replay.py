# Replays Precedence.tla: each case evaluates the spec's expression over
# symbolic operands that render the operations they perform (or runs one of
# the spec's sources), and compares the parenthesized form or the result with
# the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

NAMES = {"**": "pow", "*": "mul", "@": "matmul", "/": "truediv", "//": "floordiv", "%": "mod", "+": "add", "-": "sub",
         "<<": "lshift", ">>": "rshift", "&": "and", "^": "xor", "|": "or"}
UNARY = {"-": "neg", "+": "pos", "~": "invert"}
SOURCES = {
    "not_eq": "result = not 1 == 2",
    "not_in": "result = not 1 in [1]",
    "or_and": "result = 1 or 0 and 0",
    "and_or": "result = 0 and 1 or 2",
    "not_or": "result = not 0 or 0",
    "not_and": "result = not 1 and 0",
    "cmp_chain_bitor": "result = 1 | 2 == 3",
    "cmp_chain_mixed": "result = 1 < 2 == 2 in [2] is not None",
    "bitand_cmp": "result = 1 & 3 == 1",
    "cond_or": "result = 0 or 1 if 0 else 5",
    "cond_nested": "result = 1 if 0 else 2 if 0 else 3",
    "cond_lambda": "f = lambda: 0 if 1 else 1\nresult = f()",
    "lambda_lowest": "result = (lambda: 1, 2)[1]",
    "walrus_lowest": "result = (x := 1 + 2 * 3)",
    "await_power": "async def g():\n    return 2\nasync def f():\n    return await g() ** 2\nc = f()\ntry:\n    c.send(None)\nexcept StopIteration as e:\n    result = e.value",
    "unary_power_right": "result = 2 ** -1",
    "neg_power": "result = -2 ** 2",
    "double_neg": "result = - - 2",
    "not_not": "result = not not 2",
    "power_attr": "result = 2 ** (1).real",
    "call_before_unary": "result = -abs(-3)",
    "subscript_before_power": "result = [2][0] ** 2",
    "star_in_call": "result = max(*[1, 2] , 0)",
    "comparison_not_associative": "result = (1 < 2) < 3",
    "is_not_vs_not": "result = (1 is not None, 1 is (not None))",
    "in_not_in": "result = 1 not in [2]",
    "tuple_comma_lowest": "x = 1, 2 if 0 else 3\nresult = x",
    "yield_lowest": "def g():\n    x = yield 1, 2\n    yield x\nit = g()\nresult = next(it)",
    "string_concat_before_ops": "result = 'a' 'b' * 2",
    "unary_not_bitwise": "result = not 0 | 1",
    "invert_bool": "result = ~True",
    "starred_precedence": "result = [*range(2) or [9]]",
}


class Symbol:
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return self.text


def binary(op):
    return lambda a, b: Symbol("(%s %s %s)" % (a, op, b))


def unary(op):
    return lambda a: Symbol("(%s%s)" % (op, a))


for _op, _name in NAMES.items():
    setattr(Symbol, "__%s__" % _name, binary(_op))
for _op, _name in UNARY.items():
    setattr(Symbol, "__%s__" % _name, unary(_op))


def outcome(p):
    symbols = {"a": Symbol("a"), "b": Symbol("b"), "c": Symbol("c")}
    if "left" in p:
        return repr(eval("a %s b %s c" % (p["left"], p["right"]), symbols))
    if "unary" in p:
        form = "%sa %s b" if p["position"] == "prefix" else "a %s %sb"
        source = form % (p["unary"], p["binary"]) if p["position"] == "prefix" else form % (p["binary"], p["unary"])
        return repr(eval(source, symbols))
    namespace = {}
    try:
        exec(compile(SOURCES[p["case"]], "<case>", "exec"), namespace)
        return repr(namespace.get("result"))
    except SyntaxError as error:
        return "%s: %s" % (type(error).__name__, error.msg)
    except Exception as error:
        return "%s: %s" % (type(error).__name__, error)


check_programs(outcome)
