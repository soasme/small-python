# Replays PercentFormat.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
class P:
    def __str__(self): return 'p'
    def __repr__(self): return 'P()'
class B:
    def __bytes__(self): return b'bb'
class I:
    def __index__(self): return 7
class F:
    def __float__(self): return 1.5

SOURCES = {
    "s_r_a": "result = '%s %r %a' % ('\xe9', '\xe9', '\xe9')",
    "s_object": "result = '%s|%r|%5s|%-5s|%.1s' % (P(), P(), 'ab', 'ab', 'xyz')",
    "percent_literal": "result = '100%% %d' % 5",
    "mapping": "result = '%(language)s has %(number)03d quote types.' % {'language': 'Python', 'number': 2}",
    "mapping_missing": "result = '%(x)s' % {}",
    "mapping_needs_dict": "result = '%(x)s' % (1,)",
    "mapping_mixed": "result = '%(x)s %s' % {'x': 1}",
    "star_width": "result = '%*d|%-*d|%.*f' % (5, 1, 4, 2, 2, 3.14159)",
    "star_negative": "result = '%*d' % (-5, 1)",
    "star_not_int": "result = '%*d' % ('a', 1)",
    "single_value": "result = ('%s' % 5, '%s' % (5,), '%s' % [1, 2])",
    "tuple_value": "result = '%s' % ((1, 2),)",
    "not_enough": "result = '%s %s' % ('a',)",
    "not_all_converted": "result = '%s' % ('a', 'b')",
    "no_format_tuple": "result = 'abc' % (1,)",
    "no_format_dict": "result = 'abc' % {'a': 1}",
    "unsupported_char": "result = '%y' % 1",
    "incomplete": "result = 'abc %' % ()",
    "c_conversion": "result = ('%c' % 65, '%c' % 'z', '%c' % 0x1f600)",
    "c_bad": "result = '%c' % 'ab'",
    "c_range": "result = '%c' % -1",
    "c_float": "result = '%c' % 1.5",
    "d_float": "result = ('%d' % 2.9, '%i' % -2.9, '%d' % True)",
    "d_index": "result = '%d' % I()",
    "d_str": "result = '%d' % '1'",
    "x_float": "result = '%x' % 2.5",
    "x_index": "result = '%x' % I()",
    "f_int": "result = ('%f' % 3, '%.2f' % F())",
    "f_str": "result = '%f' % 'a'",
    "g_formats": "result = ('%g' % 0.0001, '%g' % 1e20, '%#g' % 1.0, '%G' % 1e-10, '%.3g' % 1234.5)",
    "E_F": "result = ('%E' % 1.5, '%F' % float('inf'), '%f' % float('nan'), '%5.1f' % -float('inf'))",
    "huge_int": "result = '%d' % (10 ** 30)",
    "x_negative_alt": "result = ('%#x' % -255, '%#o' % 0, '%#X' % 255)",
    "length_modifier": "result = '%ld %hd %Lf' % (1, 2, 3.0)",
    "bytes_basic": "result = b'%s %d %x %5.2f' % (b'ab', 5, 255, 2.5)",
    "bytes_b_alias": "result = b'%b|%s' % (bytearray(b'x'), memoryview(b'm'))",
    "bytes_dunder": "result = b'%s' % B()",
    "bytes_str_rejected": "result = b'%s' % 'a'",
    "bytes_r_is_a": "result = b'%r %a' % ('\xe9', '\xe9')",
    "bytes_c": "result = (b'%c' % 65, b'%c' % b'z')",
    "bytes_c_bad": "result = b'%c' % 256",
    "bytes_mapping": "result = b'%(k)s' % {b'k': b'v'}",
    "bytes_percent": "result = b'%%%d' % 1",
    "bytearray_result": "result = bytearray(b'%d') % 5",
    "bytes_not_all": "result = b'%d' % (1, 2)",
    "bytes_unsupported": "result = b'%y' % 1",
    "bytes_float": "result = b'%.1e' % 12345.0"
}


TYPES = {name: value for name, value in list(globals().items()) if isinstance(value, type) and name[0].isupper()}


def generated(p):
    spec = "%" + "".join(sorted(p["flags"])) + (str(p["width"]) if p["width"] else "")
    spec += ("." + str(p["prec"]) if p["prec"] >= 0 else "") + p["type"]
    value = p["n"] if p["kind"] == "int" else p["num"] / 8
    return repr(spec.encode() % value if p["target"] == "bytes" else spec % value)


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
