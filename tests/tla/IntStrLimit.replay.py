# Replays IntStrLimit.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
from harness import host

LIMITS = [0, 640, 1000]
DIGITS = [639, 640, 641, 999, 1000, 1001, 4300, 4301]
OPS = ["str", "neg_str", "int", "int_neg", "underscore", "int7", "int16"]


def limited(limit, digits, op):
    old = host.int_max_str_digits()
    host.set_int_max_str_digits(limit)
    try:
        if op == "str": return repr(len(str(10 ** (digits - 1))))
        if op == "neg_str": return repr(len(str(-10 ** (digits - 1))))
        if op == "int": return repr(len(str(int("1" * digits))))
        if op == "int_neg": return repr(int("-" + "1" * digits) < 0)
        if op == "underscore": return repr(int("1_" * (digits - 1) + "1") > 0)
        if op == "int7": return repr(int("1" * digits, 7) > 0)
        if op == "int16": return repr(len(hex(int("1" * digits, 16))) - 2)
    except ValueError as error:
        return "ValueError: %s" % error
    finally:
        host.set_int_max_str_digits(old)

SOURCES = {
    "default": 'from harness import host\nresult = host.int_max_str_digits()',
    "str_over": 'result = len(str(10 ** 4300))',
    "str_at_limit": 'result = len(str(10 ** 4299))',
    "int_over": "result = int('1' * 4301)",
    "int_at_limit": "result = len(str(int('1' * 4300)))",
    "underscores_ignored": "result = int('1_' * 4300 + '1') > 0",
    "leading_zeros_count": "result = int('0' * 4301)",
    "hex_unlimited": "result = int('f' * 5000, 16).bit_length()",
    "base_8_unlimited": 'result = len(oct(10 ** 5000))',
    "base_10_explicit": "result = int('1' * 4301, 10)",
    "base_7_limited": "result = int('1' * 4301, 7)",
    "base_0": "result = int('1' * 4301, 0)",
    "set_limit": 'from harness import host\nold = host.int_max_str_digits()\nhost.set_int_max_str_digits(640)\ntry:\n    result = (len(str(10 ** 639)), host.int_max_str_digits())\n    try:\n        str(10 ** 640)\n    except ValueError as e:\n        result += (str(e),)\nfinally:\n    host.set_int_max_str_digits(old)',
    "set_zero": 'from harness import host\nold = host.int_max_str_digits()\nhost.set_int_max_str_digits(0)\ntry:\n    result = len(str(10 ** 10000))\nfinally:\n    host.set_int_max_str_digits(old)',
    "set_too_small": 'from harness import host\nhost.set_int_max_str_digits(639)',
    "set_negative": 'from harness import host\nhost.set_int_max_str_digits(-1)',
    "set_keyword": 'from harness import host\nold = host.int_max_str_digits()\nhost.set_int_max_str_digits(maxdigits=1000)\nresult = host.int_max_str_digits()\nhost.set_int_max_str_digits(old)',
    "set_type": "from harness import host\nhost.set_int_max_str_digits('1000')",
    "repr_over": 'result = repr(10 ** 4300)',
    "format_d_over": "result = '{:d}'.format(10 ** 4300)",
    "fstring_over": "x = 10 ** 4300\nresult = f'{x}'",
    "percent_over": "result = '%d' % (10 ** 4300)",
    "format_x_ok": "result = len(format(10 ** 4300, 'x'))",
    "float_unaffected": "result = float('1' * 5000)",
    "int_from_bytes": "result = int(b'1' * 4301)",
    "int_bytearray": "result = int(bytearray(b'1' * 4301))",
    "negative_str": 'result = len(str(-10 ** 4299))',
    "negative_over": 'result = str(-10 ** 4300)',
    "int_sign_over": "result = int('-' + '1' * 4301)",
    "literal_over": "result = eval('1' * 4301)",
    "literal_hex": "result = eval('0x' + 'f' * 5000).bit_length()",
    "decimal_digits_check": "result = int(' ' * 5000 + '1' * 10 + ' ' * 5000)",
    "int_subclass_str": 'class I(int): pass\nresult = str(I(10 ** 4300))',
    "error_message_int": "try:\n    int('1' * 4301)\nexcept ValueError as e:\n    result = str(e)"
}




def generated(p):
    return limited(p["limit"], p["digits"], p["op"])


def run(p):
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


def outcome(p):
    # TLA+ strings are ASCII.
    return run(p).encode("ascii", "backslashreplace").decode()


check_programs(outcome)
