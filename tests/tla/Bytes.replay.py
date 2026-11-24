# Replays Bytes.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
class B:
    def __bytes__(self): return b'dunder'
class I:
    def __index__(self): return 3
class J:
    def __init__(self, v, log): self.v, self.log = v, log
    def __index__(self):
        for _ in ():  # a loop: __index__ runs on the machine
            pass
        self.log.append(self.v)
        return self.v

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
    "bytearray_arity": "ba = bytearray(b'ab')\ndef m(f):\n    try: f()\n    except TypeError as e: return str(e)\n"
                       "result = (m(lambda: ba.append()), m(lambda: ba.pop(1, 2)), m(lambda: ba.insert(0)), m(lambda: ba.clear(1)), m(lambda: ba.remove(x=1)))",
    "search_needle_last": "log = []\nclass X:\n    def __init__(self, v): self.v = v\n    def __index__(self):\n        for _ in (): pass\n        log.append(self.v)\n        return self.v\nb = b\"abcb\"\nresult = (b.find(X(98), X(2)), bytes.count(b, X(98), X(0), X(4)), bytearray(b).rfind(X(98), 0, X(3)), log)",
    "bytes_item_index": "log = []\nclass V:\n    def __init__(self, v): self.v = v\n    def __index__(self):\n        for _ in (): pass\n        log.append(self.v)\n        return self.v\n"
                        "def gen(*x): yield from x\nb = bytearray(b'q')\nb.extend(gen(V(67)))\n"
                        "result = (bytes(gen(V(65), V(66))), b, bytes([V(65), V(68)]), log)",
    "bytearray_store_calls": "ba = bytearray(b'abc')\nclass V:\n    def __init__(self, v, rep): self.v, self.rep = v, rep\n    def __index__(self):\n        for _ in (): pass\n        ba[:] = self.rep\n        return self.v\n"
                             "ba[0] = V(65, b'xb')\nr = bytes(ba)\ntry: ba[1] = V(66, b'')\nexcept IndexError as e: i = type(e).__name__\n"
                             "try: ba[0] = V(256, b'')\nexcept ValueError as e: v = str(e)\nresult = (r, i, bytes(ba), v)",
    "bytearray_take_calls": "ba = bytearray(b'abc')\nclass R:\n    def __index__(self):\n        for _ in (): pass\n        ba[:] = b'xbxb'\n        return 2\n"
                            "t = ba.take_bytes(R())\nr = (t, bytes(ba), ba.resize(R()) if ba.extend(b'xb') is None else 0, bytes(ba) + b'' if ba.resize(5) is None else 0)\n"
                            "try: ba.take_bytes(1.5)\nexcept TypeError as e: m = str(e)\ntry: ba.resize(-1)\nexcept ValueError as e: v = str(e)\nresult = r + (m, v)",
    "bytearray_index_calls": "ba = bytearray(b'abc')\nclass R:\n    def __index__(self):\n        ba[:] = b'xbxb'\n        return 2\n"
                             "log = []\nclass L:\n    def __index__(self):\n        for _ in (): pass\n        log.append(1)\n        return 1\n"
                             "f = ba.count(b'b', R())\ng = bytes(ba)\n"
                             "result = (f, g, ba.pop(L()), ba.find(b'b', None, L()), ba.insert(L(), 97), bytes(ba), len(log))",
    "hex_group_first": "log = []\nclass G:\n    def __index__(self):\n        log.append(1)\n        return 1\n"
                       "def bad():\n    try: return b'ab'.hex('::', G())\n    except ValueError as e: return type(e).__name__\n"
                       "result = (bad(), b'ab'.hex(':', bytes_per_sep=G()), len(log))",
    "literal_forms": 'result = (b\'still allows embedded "double" quotes\', b"a\'b", b\'\'\'3\'\'\', rb\'\\d\', len(b\'\\x00\'))',
    "literal_non_ascii": 'compile("b\'\\u00e9\'", \'s\', \'eval\')',
    "ctor_forms": "result = (bytes(), bytes(3), bytes(range(3)), bytes(b'ab'), bytes(bytearray(b'c')), bytes(memoryview(b'm')), bytes(B()), bytes(I()))",
    "ctor_str_encoding": "result = (bytes('\xe9', 'utf-8'), bytes('\xe9', encoding='latin-1'), bytes('a', 'ascii', 'strict'))",
    "hex_sep_length": "log = []\nclass T(str):\n    def __len__(self):\n        for _ in (): pass\n        log.append('len')\n        return 1\n"
                      "class Two(bytes):\n    def __len__(self):\n        log.append('len')\n        return 2\n"
                      "class G:\n    def __index__(self):\n        for _ in (): pass\n        log.append('index')\n        return 2\n"
                      "def bad():\n    try: return b'ab'.hex(Two(b':'))\n    except ValueError as e: return type(e).__name__\n"
                      "result = (b'abcd'.hex(T(':'), G()), memoryview(b'ab').hex(sep=T('.')), bad(), log)",
    "ctor_subclass_index": "log = []\nclass C(bytes):\n    def __index__(self):\n        for _ in (): pass\n        log.append(3)\n        return 3\n"
                           "class L(list):\n    def __index__(self):\n        for _ in (): pass\n        log.append(2)\n        return 2\n"
                           "class N(int):\n    def __index__(self): return 4\n"
                           "result = (bytearray(C(b'abcd')), bytes(L([9])), bytearray(N(1)), log)",
    "ctor_size_fallback": "log = []\nclass U:\n    def __index__(self):\n        for _ in (): pass\n        log.append('index')\n        raise TypeError\n"
                          "    def __buffer__(self, flags): log.append('buffer'); return memoryview(b'xy')\n"
                          "class N:\n    def __index__(self): log.append('index'); raise TypeError\n"
                          "    def __iter__(self):\n        log.append('iter')\n        yield 7\n"
                          "result = (bytes(U()), bytearray(U()), bytes(N()), bytearray(N()), log)",
    "ctor_iter_calls": "class It:\n    def __init__(s, items, log): s.items, s.log = items, log\n"
                       "    def __iter__(s):\n        for _ in (): pass\n        s.log.append('iter')\n        return iter(s.items)\n"
                       "    def __len__(s): s.log.append('len'); return 2\n"
                       "class N:\n    def __iter__(s):\n        for _ in (): pass\n        return 5\n"
                       "log = []\ntry: bytes(N())\nexcept TypeError as e: refused = f'TypeError: {e}'\n"
                       "result = (bytes(It([97, 98], log)), bytearray(It((1,), log)), log, refused)",
    "extend_iter_calls": "class It:\n    def __init__(s, items, log): s.items, s.log = items, log\n"
                         "    def __iter__(s):\n        for _ in (): pass\n        s.log.append('iter')\n        return iter(s.items)\n"
                         "    def __len__(s): s.log.append('len'); return 2\n"
                         "class N:\n    def __iter__(s):\n        for _ in (): pass\n        return 5\n"
                         "log = []\nb = bytearray(b'x')\ndone = b.extend(It([97, 98], log))\n"
                         "try: b.extend(N())\nexcept TypeError as e: refused = f'TypeError: {e}'\n"
                         "result = (done, bytearray(b), log, refused, b)",
    "join_iter_calls": "class It:\n    def __init__(s, log): s.log = log\n"
                       "    def __iter__(s):\n        for _ in (): pass\n        s.log.append('iter')\n        return iter([b'a', b'b'])\n"
                       "class N:\n    def __iter__(s):\n        for _ in (): pass\n        return 5\n"
                       "log = []\ntry: b''.join(N())\nexcept TypeError as e: refused = str(e)\n"
                       "result = (b'-'.join(It(log)), bytearray(b'+').join(It(log)), bytes.join(b'-', (x for x in [b'a', b'b'])), log, refused)",
    "ctor_index_calls": "log = []\nresult = (bytes(J(2, log)), bytearray(J(1, log)), log)",
    "ctor_index_big": "result = bytes(J(1 << 70, []))",
    "ctor_negative": 'result = bytes(-1)',
    "ctor_range_error": 'result = bytes([256])',
    "ctor_float": 'result = bytes(1.5)',
    "bytearray_ctor": "result = (bytearray(), bytearray(2), bytearray(b'ab'), bytearray('\xe9', 'utf-8'), bytearray(range(2)))",
    "fromhex": "result = (bytes.fromhex('2Ef0 F1f2  '), bytearray.fromhex('2ef0'), bytes.fromhex(''), bytes.fromhex(b'00'))",
    "fromhex_subclass": ("class A(bytearray):\n    def __init__(self, v):\n        for _ in (): pass\n"
                         "        log.append(type(v).__name__)\n        bytearray.__init__(self, v)\n"
                         "log = []\na = A.fromhex('2e')\nresult = (log, type(a).__name__, bytes(a))"),
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
    "contains_index": "log = []\nresult = (J(98, log) in b'abc', J(120, log) not in b'abc', (0, J(99, log) in b'c', 1), log)",
    "contains_index_fails": "result = J('s', []) in b'abc'",
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
    "decode_unicode_escape": "result = (b'\\xc3\\xa9'.decode('unicode_escape'), b'a\\\\n\\\\x41\\\\101\\\\u00e9\\\\N{BULLET}\\\\q'.decode('unicode-escape'), b'\\\\x4'.decode('unicode_escape', 'backslashreplace'))",
    "decode_unicode_escape_error": "result = b'ab\\\\x4'.decode('unicode_escape')",
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
