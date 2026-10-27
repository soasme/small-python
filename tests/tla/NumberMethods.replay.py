# Replays NumberMethods.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
class F:
    def __float__(self): return 2.5
class I:
    def __index__(self): return 7
class C:
    def __complex__(self): return 1+2j
class FI:
    def __float__(self): return 1.5
    def __index__(self): return 9
class BB:
    def __bytes__(self): return b'xy'
    def __iter__(self): return iter([1])
class Bad:
    def __iter__(self): raise TypeError('boom')
class Boom:
    def __iter__(self): raise ValueError('boom')

SOURCES = {
    "to_bytes_default": "result = (65).to_bytes()",
    "to_bytes_default_overflow": "result = (256).to_bytes()",
    "to_bytes_bad_order": "result = (1).to_bytes(1, 'middle')",
    "to_bytes_negative_length": "result = (1).to_bytes(-1)",
    "to_bytes_signed_keyword_only": "result = (1).to_bytes(1, 'big', True)",
    "to_bytes_length_index": "result = (1).to_bytes(I(), 'little')",
    "to_bytes_length_float": "result = (1).to_bytes(1.0)",
    "to_bytes_order_type": "result = (1).to_bytes(1, b'big')",
    "from_bytes_iterable": "result = int.from_bytes([255, 0, 0], byteorder='big')",
    "from_bytes_bytearray": "result = int.from_bytes(bytearray(b'\\x01\\x00'), 'little')",
    "from_bytes_empty_signed": "result = int.from_bytes(b'', signed=True)",
    "from_bytes_bad_item": "result = int.from_bytes([256])",
    "from_bytes_not_iterable": "result = int.from_bytes(5)",
    "from_bytes_str": "result = int.from_bytes('ab')",
    "from_bytes_bad_order": "result = int.from_bytes(b'\\x01', 'middle')",
    "from_bytes_subclass": "class Sub(int): pass\nresult = (type(Sub.from_bytes(b'\\x05')).__name__, Sub.from_bytes(b'\\x05'))",
    "from_bytes_bool": "result = bool.from_bytes(b'\\x01')",
    "as_integer_ratio_int": "result = ((-7).as_integer_ratio(), True.as_integer_ratio(), type(True.as_integer_ratio()[0]).__name__)",
    "is_integer_int": "result = (5).is_integer()",
    "bit_length_huge": "result = (1 << 1000).bit_length()",
    "bit_count_huge": "result = ((1 << 1000) - 1).bit_count()",
    "bool_bit_length": "result = True.bit_length()",
    "float_from_number_int": "result = float.from_number(3)",
    "float_from_number_big": "result = float.from_number(10 ** 400)",
    "float_from_number_dunder": "result = float.from_number(F())",
    "float_from_number_index": "result = float.from_number(I())",
    "float_from_number_both": "result = float.from_number(FI())",
    "float_from_number_str": "result = float.from_number('1.5')",
    "float_from_number_bool": "result = float.from_number(True)",
    "float_ratio": "result = (0.75).as_integer_ratio()",
    "float_ratio_negative": "result = (-0.1).as_integer_ratio()",
    "float_ratio_inf": "result = float('inf').as_integer_ratio()",
    "float_ratio_nan": "result = float('nan').as_integer_ratio()",
    "float_ratio_zero": "result = (-0.0).as_integer_ratio()",
    "float_is_integer": "result = ((-2.0).is_integer(), (3.2).is_integer(), float('inf').is_integer(), float('nan').is_integer(), 1e300.is_integer())",
    "float_hex": "result = (3740.0).hex()",
    "float_hex_special": "result = (float('inf').hex(), float('-inf').hex(), float('nan').hex(), (0.0).hex(), (-0.0).hex())",
    "float_hex_subnormal": "result = (5e-324).hex()",
    "float_hex_max": "result = (1.7976931348623157e308).hex()",
    "float_hex_one": "result = (1.0).hex(), (0.1).hex()",
    "fromhex_example": "result = float.fromhex('0x3.a7p10')",
    "fromhex_whitespace": "result = float.fromhex('  -0x1p-2  ')",
    "fromhex_no_prefix": "result = float.fromhex('ff')",
    "fromhex_fraction_only": "result = float.fromhex('.8')",
    "fromhex_case": "result = float.fromhex('0X1.8P+1')",
    "fromhex_special": "result = (float.fromhex('inf'), float.fromhex('-Infinity'), float.fromhex('nan'))",
    "fromhex_no_digits": "result = float.fromhex('0x.p1')",
    "fromhex_garbage": "result = float.fromhex('0x1g')",
    "fromhex_overflow": "result = float.fromhex('0x1p1024')",
    "fromhex_underflow": "result = float.fromhex('0x1p-1080')",
    "fromhex_round": "result = float.fromhex('0x1.00000000000008p0')",
    "fromhex_round_odd": "result = float.fromhex('0x1.00000000000018p0')",
    "fromhex_subclass": "class G(float): pass\nresult = type(G.fromhex('0x1p0')).__name__",
    "fromhex_not_str": "result = float.fromhex(1)",
    "hex_roundtrip": "xs = [0.1, -2.5, 1e-310, 123456.789]\nresult = all(float.fromhex(x.hex()) == x for x in xs)",
    "complex_from_number_float": "result = complex.from_number(2.5)",
    "complex_from_number_dunder": "result = complex.from_number(C())",
    "complex_from_number_float_dunder": "result = complex.from_number(F())",
    "complex_from_number_index": "result = complex.from_number(I())",
    "complex_from_number_str": "result = complex.from_number('1+2j')",
    "complex_from_number_complex": "result = complex.from_number(3j)",
    "float_hex_method_on_int": "result = float.hex(3)",
    "fromhex_instance": "result = (1.0).fromhex('0x2p0')",
    "from_bytes_index_object": "result = int.from_bytes(I())",
    "from_bytes_float": "result = int.from_bytes(1.5)",
    "from_bytes_dunder_bytes": "result = int.from_bytes(BB())",
    "from_bytes_iter_typeerror": "result = int.from_bytes(Bad())",
    "from_bytes_iter_valueerror": "result = int.from_bytes(Boom())",
    "from_bytes_order_type": "result = int.from_bytes(b'1', b'big')",
    "to_bytes_too_many": "result = (1).to_bytes(1, 'big', True, 4)",
    "bytes_from_float": "result = bytes(1.5)",
    "bytearray_from_none": "result = bytearray(None)",
    "bytearray_ignores_dunder_bytes": "result = bytearray(BB())",
    "bytes_uses_dunder_bytes": "result = bytes(BB())",
    "bytearray_iter_typeerror": "result = bytearray(Bad())",
    "bytes_iter_valueerror": "result = bytes(Boom())",
    "bytearray_count": "result = bytearray(I())",
    "fromhex_bytes": "result = float.fromhex(b'0x1p0')"
}


TYPES = {name: value for name, value in list(globals().items()) if isinstance(value, type) and name[0].isupper()}


def generated(p):
    try:
        if p["method"] == "to_bytes":
            return repr(list(p["n"].to_bytes(p["length"], p["order"], signed=p["signed"])))
        if p["method"] == "from_bytes":
            return repr(int.from_bytes(bytes(p["bytes"]), p["order"], signed=p["signed"]))
        return repr(getattr(p["n"], p["method"])())
    except Exception as error:
        return "%s: %s" % (type(error).__name__, error)


def outcome(p):
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


check_programs(outcome)
