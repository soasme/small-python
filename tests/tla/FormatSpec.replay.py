# Replays FormatSpec.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
class P:
    x = 3
    y = [4, 5]
    def __format__(self, spec): return 'P[' + spec + ']'
    def __repr__(self): return 'P()'
    def __str__(self): return 'p'
class BadFormat:
    def __format__(self, spec): return 5

SOURCES = {
    "str_align": "result = (format('ab', '<5'), format('ab', '>5'), format('ab', '^5'), format('ab', '*^6'), format('ab', '5'))",
    "str_precision": "result = (format('abcdef', '.3'), format('abcdef', '>6.2'))",
    "str_equal_align": "result = format('ab', '=5')",
    "str_sign": "result = format('ab', '+')",
    "str_type_bad": "result = format('ab', 'd')",
    "str_grouping": "result = format('ab', ',')",
    "str_alternate": "result = format('ab', '#')",
    "int_precision": "result = format(5, '.2')",
    "int_c": "result = (format(65, 'c'), format(0x1f600, 'c'))",
    "int_c_sign": "result = format(65, '+c')",
    "int_c_range": "result = format(-1, 'c')",
    "int_n": "result = (format(1234567, 'n'), format(-5, 'n'))",
    "int_n_grouping": "result = format(1234, ',n')",
    "int_float_types": "result = (format(5, 'f'), format(5, 'e'), format(5, '%'), format(5, 'g'))",
    "int_z": "result = format(5, 'z')",
    "int_bad_type": "result = format(5, 's')",
    "bool_formats": "result = (format(True, ''), format(True, 'd'), format(False, '>5'), f'{True:x}')",
    "float_default": "result = (format(1.5, ''), format(1e16, ''), format(1e-5, ''), format(1.0, '.3'), format(123456.0, '.3'))",
    "float_g": "result = (format(0.0001234, 'g'), format(123456789.0, 'g'), format(100.0, 'g'), format(100.0, '#g'), format(1.5, '.0g'))",
    "float_upper": "result = (format(1e20, 'E'), format(float('inf'), 'F'), format(float('nan'), 'E'), format(-float('inf'), 'f'))",
    "float_special_width": "result = (format(float('inf'), '08'), format(float('nan'), '+f'))",
    "float_alternate": "result = (format(2.0, '#.0f'), format(2.0, '#.0e'))",
    "float_c": "result = format(1.5, 'c')",
    "float_grouping_frac": "result = format(1234567.125, ',.3f')",
    "float_underscore": "result = format(1234567.0, '_.1f')",
    "float_negative_zero": "result = (format(-0.0, 'f'), format(-0.0, 'zf'), format(-0.0001, 'z.2f'))",
    "complex_format": "result = (format(1+2j, ''), format(1+2j, '.1f'), format(-1j, '+'), format(1+2j, '^20'))",
    "complex_zero_pad": "result = format(1+2j, '010')",
    "complex_equal": "result = format(1+2j, '=10')",
    "fill_brace": "result = format(5, '{^5')",
    "fill_unicode": "result = format(5, '\xe9^5')",
    "width_huge": "result = format(5, '9' * 30)",
    "invalid_spec": "result = format(5, '<<<')",
    "precision_too_big": "result = format(1.5, '.' + '9' * 25)",
    "format_dunder": "result = (format(P(), 'abc'), f'{P():xyz}', '{:q}'.format(P()))",
    "format_bad_return": 'result = format(BadFormat())',
    "object_format_nonempty": "result = format(object(), 'd')",
    "object_format_empty": "class O:\n    def __str__(self): return 'o'\nresult = format(O(), '')",
    "format_spec_type": 'result = format(5, 1)',
    "str_format_positional": "result = '{0}, {1}, {0}'.format('a', 'b')",
    "str_format_auto": "result = '{}, {}'.format('a', 'b')",
    "str_format_mixed": "result = '{0} {}'.format('a', 'b')",
    "str_format_mixed_auto_first": "result = '{} {0}'.format('a', 'b')",
    "str_format_keywords": "result = '{name}{x}'.format(name='n', x=1)",
    "str_format_attr_index": "result = '{0.x} {0.y[1]} {k[a]}'.format(P(), k={'a': 9})",
    "str_format_index_int_key": "result = '{0[0]}'.format({0: 'int', '0': 'str'})",
    "str_format_conversions": "result = '{0!r} {0!s} {0!a} {1!r}'.format(P(), '\xe9')",
    "str_format_bad_conversion": "result = '{0!x}'.format(1)",
    "str_format_nested": "result = '{0:{1}{2}}'.format(3.14159, '.', 3)",
    "str_format_nested_too_deep": "result = '{0:{1:{2}}}'.format(1, 2, 3)",
    "str_format_braces": "result = '{{}} {{{0}}}'.format(7)",
    "str_format_single_close": "result = 'a}b'.format()",
    "str_format_single_open": "result = 'a{b'.format()",
    "str_format_missing_index": "result = '{2}'.format(1)",
    "str_format_missing_key": "result = '{k}'.format()",
    "str_format_missing_auto": "result = '{} {}'.format(1)",
    "str_format_empty_attr": "result = '{0.}'.format(1)",
    "str_format_index_unclosed": "result = '{0[}'.format(1)",
    "str_format_negative_index": "result = '{-1}'.format(1)",
    "str_format_conversion_then_spec": "result = '{0!r:>6}'.format('a')",
    "str_format_example_align": "result = ('{:<30}'.format('left aligned'), '{:*^30}'.format('centered'))",
    "str_format_example_bases": "result = 'int: {0:d};  hex: {0:x};  oct: {0:o};  bin: {0:b}'.format(42)",
    "str_format_example_prefix": "result = 'int: {0:d};  hex: {0:#x};  oct: {0:#o};  bin: {0:#b}'.format(42)",
    "str_format_example_percent": "result = 'Correct answers: {:.2%}'.format(19/22)",
    "str_format_example_comma": "result = '{:,}'.format(1234567890)",
    "str_format_example_nesting": "result = [ '{0:{fill}{align}16}'.format('text', fill=align, align=align) for align in '<^>' ]",
    "str_format_example_items": "c = 3-5j\nresult = ('The complex number {0} is formed from the real part {0.real} and the imaginary part {0.imag}.').format(c)",
    "str_format_extra_args": "result = '{0}'.format(1, 2, x=3)",
    "format_map_missing": "result = '{a}'.format_map({})",
    "fstring_format_spec": 'w = 6\nresult = f\'{3.14159:{w}.2f}|{"x"!r:^5}\'',
    "format_builtin_default": "result = (format(5), format('a'), format(None))"
}


TYPES = {name: value for name, value in list(globals().items()) if isinstance(value, type) and name[0].isupper()}


def generated(p):
    width = str(p["width"]) if p["width"] else ""
    if p["kind"] == "int":
        value, spec = p["n"], p["align"] + p["sign"] + p["alt"] + p["zero"] + width + p["group"] + p["type"]
    else:
        precision = "." + str(p["prec"]) if p["prec"] >= 0 else ""
        value = p["num"] / 8
        spec = p["align"] + p["sign"] + p["z"] + p["zero"] + width + p["group"] + precision + p["type"]
    try:
        return repr(format(value, spec))
    except ValueError as error:
        return "ValueError: %s" % error


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
