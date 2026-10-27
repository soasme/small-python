# Replays Bytes.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
class B:
    def __bytes__(self): return b'dunder'
class I:
    def __index__(self): return 3

SEARCH = ["find", "rfind", "count", "startswith", "endswith", "partition", "rpartition", "split", "rsplit1",
          "replace", "replace1", "removeprefix", "removesuffix", "strip", "lstrip", "rstrip", "index"]
WHOLE = ["split_ws", "rsplit_ws1", "strip_ws"]
PAD = ["center", "ljust", "rjust", "zfill"]


def search(method, s, t, kind):
    s, t = kind(s.encode()), t.encode()
    try:
        if method == "rsplit1": return repr(s.rsplit(t, 1))
        if method == "replace": return repr(s.replace(t, b"X"))
        if method == "replace1": return repr(s.replace(t, b"X", 1))
        if method == "split_ws": return repr(s.split())
        if method == "rsplit_ws1": return repr(s.rsplit(None, 1))
        if method == "strip_ws": return repr(s.strip())
        return repr(getattr(s, method)(t))
    except ValueError as e:
        return "ValueError: %s" % e


def pad(method, s, width, kind):
    s = kind(s.encode())
    return repr(s.zfill(width) if method == "zfill" else getattr(s, method)(width, b"*"))



SOURCES = {
    "literal_forms": 'result = (b\'still allows embedded "double" quotes\', b"a\'b", b\'\'\'3\'\'\', rb\'\\d\', len(b\'\\x00\'))',
    "literal_non_ascii": 'compile("b\'\\u00e9\'", \'s\', \'eval\')',
    "ctor_forms": "result = (bytes(), bytes(3), bytes(range(3)), bytes(b'ab'), bytes(bytearray(b'c')), bytes(memoryview(b'm')), bytes(B()), bytes(I()))",
    "ctor_str_encoding": "result = (bytes('\xe9', 'utf-8'), bytes('\xe9', encoding='latin-1'), bytes('a', 'ascii', 'strict'))",
    "ctor_negative": 'result = bytes(-1)',
    "ctor_range_error": 'result = bytes([256])',
    "ctor_float": 'result = bytes(1.5)',
    "bytearray_ctor": "result = (bytearray(), bytearray(2), bytearray(b'ab'), bytearray('\xe9', 'utf-8'), bytearray(range(2)))",
    "fromhex": "result = (bytes.fromhex('2Ef0 F1f2  '), bytearray.fromhex('2ef0'), bytes.fromhex(''), bytes.fromhex(b'00'))",
    "fromhex_bad": "result = bytes.fromhex('2e f')",
    "fromhex_space_middle": "result = bytes.fromhex('2 e')",
    "fromhex_non_hex": "result = bytes.fromhex('zz')",
    "hex": "result = (b'\\xf0\\xf1\\xf2'.hex(), b'\\xf0\\xf1\\xf2'.hex('-'), b'UUDDLRLRAB'.hex(' ', 4), b'UUDDLRLRAB'.hex(':', -4), bytearray(b'\\x01').hex())",
    "hex_bad_sep": "result = b'ab'.hex('--')",
    "index_is_int": "b = b'abc'\nresult = (b[0], b[0:1], b[-1], type(b[0]).__name__)",
    "iterate_ints": "result = list(b'ab')",
    "repr_escapes": 'result = (b\'\\x00\\t\\n\\r\\\\\\\'\\x7f\\x80\', bytearray(b\'"\'))',
    "immutable": "b = b'ab'\nb[0] = 1",
    "concat_repeat": "result = (b'ab' + b'cd', b'ab' + bytearray(b'c'), bytearray(b'a') + b'b', b'ab' * 2, 2 * bytearray(b'x'))",
    "concat_str": "result = b'a' + 'b'",
    "contains": "result = (98 in b'abc', b'bc' in b'abc', bytearray(b'b') in b'abc', 300 in b'abc')",
    "contains_str": "result = 'a' in b'abc'",
    "compare": "result = (b'a' == bytearray(b'a'), b'a' < b'b', b'a' == 'a', bytearray(b'b') > b'a')",
    "hash": "result = hash(b'ab') == hash(b'ab')",
    "hash_bytearray": "result = hash(bytearray(b'a'))",
    "count_int": "result = (b'abcb'.count(98), b'abcb'.find(99), b'abc'.index(b'c'), bytearray(b'aa').rfind(97))",
    "count_range": "result = b'abc'.count(256)",
    "search_str": "result = b'abc'.find('a')",
    "case_ascii_only": "result = (b'aB\\xe9'.upper(), b'Ab\\xc9'.lower(), b'hello world'.title(), b'aB'.swapcase(), b'hELLO'.capitalize())",
    "predicates": "result = (b'abc'.isalpha(), b'ab1'.isalnum(), b'\\xe9'.isalpha(), b'12'.isdigit(), b' \\t'.isspace(), b'Ab'.istitle(), b'AB'.isupper(), b'ab'.islower(), b'\\x7f'.isascii(), b''.isalpha())",
    "expandtabs": "result = (b'01\\t012\\t0123\\t01234'.expandtabs(), b'a\\tb'.expandtabs(4))",
    "splitlines": "result = (b'ab c\\n\\nde fg\\rkl\\r\\n'.splitlines(), b'a\\nb'.splitlines(keepends=True), b'a\\x0bb'.splitlines())",
    "split_maxsplit": "result = (b'1,2,3'.split(b',', maxsplit=1), b'  1  2  '.split(), b'a,b'.rsplit(b',', 1))",
    "split_str_sep": "result = b'a'.split('a')",
    "join": "result = (b'-'.join([b'a', bytearray(b'b'), memoryview(b'c')]), bytearray(b',').join([b'x', b'y']))",
    "join_str": "result = b''.join(['a'])",
    "maketrans_translate": "t = bytes.maketrans(b'abc', b'xyz')\nresult = (len(t), b'aabbcc'.translate(t), b'read this short text'.translate(None, b'aeiou'))",
    "maketrans_unequal": "result = bytes.maketrans(b'ab', b'x')",
    "translate_bad_table": "result = b'a'.translate(b'short')",
    "zfill": "result = (b'42'.zfill(5), b'-42'.zfill(5), bytearray(b'+1').zfill(4))",
    "replace_count": "result = (b'aaa'.replace(b'a', b'b', 2), b'abc'.replace(b'', b'-'))",
    "decode": "result = (b'caf\\xc3\\xa9'.decode(), b'\\xe9'.decode('latin-1'), b'\\xff'.decode('utf-8', 'replace'), b'\\xff'.decode('ascii', 'ignore'))",
    "decode_error": "result = b'\\xff'.decode()",
    "removeprefix_types": "result = (b'abc'.removeprefix(bytearray(b'a')), bytearray(b'abc').removesuffix(b'c'))",
    "strip_bytes_arg": "result = (b'xxaxx'.strip(b'x'), b'  a  '.strip(), bytearray(b'ab').lstrip(b'a'))",
    "bytearray_mutations": "a = bytearray(b'abc')\na[0] = 120\na[1:2] = b'YY'\na.append(33)\na.extend(b'!?')\na.insert(0, 62)\nx = a.pop()\na.remove(33)\ndel a[0]\nresult = (a, x)",
    "bytearray_methods": "a = bytearray(b'abc')\na.reverse()\nb = a.copy()\na.clear()\nresult = (a, b, b is not a)",
    "bytearray_inplace": "a = bytearray(b'ab')\nb = a\na += b'c'\na *= 2\nresult = (a, b is a)",
    "bytearray_setitem_range": "a = bytearray(b'a')\na[0] = 256",
    "bytearray_append_bad": "a = bytearray()\na.append(b'x')",
    "bytearray_remove_missing": "a = bytearray(b'a')\na.remove(98)",
    "bytearray_pop_empty": 'bytearray().pop()',
    "bytearray_slice_assign_int": "a = bytearray(b'abc')\na[0:1] = 5\nresult = a",
    "bytearray_slice_assign_str": "a = bytearray(b'abc')\na[0:1] = 'x'",
    "bytearray_extended_slice": "a = bytearray(b'abcdef')\na[::2] = b'XYZ'\nresult = a",
    "bytearray_extended_slice_size": "a = bytearray(b'abcdef')\na[::2] = b'XY'",
    "bytearray_resize_exported": "a = bytearray(b'abc')\nm = memoryview(a)\na.append(1)",
    "bytearray_methods_return_new": "a = bytearray(b'ab')\nresult = (a.upper() is a, type(a.strip()).__name__, type(a[0:1]).__name__)",
    "bytes_methods_on_bytearray_args": "result = b'abc'.startswith((bytearray(b'a'), b'z'))",
    "isascii_empty": "result = (b''.isascii(), bytearray().isspace())",
    "len_and_bool": "result = (len(b''), bool(b''), bool(b'\\x00'))"
}


TYPES = {name: value for name, value in list(globals().items()) if isinstance(value, type) and name[0].isupper()}
KINDS = {"bytes": bytes, "bytearray": bytearray}


def generated(p):
    s = "".join(p["s"])
    if p["method"] in PAD:
        return pad(p["method"], s, p["width"], KINDS[p["kind"]])
    return search(p["method"], s, "".join(p.get("t", ())), KINDS[p["kind"]])


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
