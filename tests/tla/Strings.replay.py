# Replays Strings.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
class S:
    def __str__(self): return 'S!'
class NoStr:
    def __repr__(self): return 'NoStr()'
class BadStr:
    def __str__(self): return 5
class Sub(str):
    pass

SEARCH = ["find", "rfind", "count", "startswith", "endswith", "partition", "rpartition", "split", "rsplit1",
          "replace", "replace1", "removeprefix", "removesuffix", "strip", "lstrip", "rstrip", "index"]
WHOLE = ["split_ws", "rsplit_ws1", "strip_ws"]
PAD = ["center", "ljust", "rjust", "zfill"]


def search(method, s, t):
    try:
        if method == "rsplit1": return repr(s.rsplit(t, 1))
        if method == "replace": return repr(s.replace(t, "X"))
        if method == "replace1": return repr(s.replace(t, "X", 1))
        if method == "split_ws": return repr(s.split())
        if method == "rsplit_ws1": return repr(s.rsplit(None, 1))
        if method == "strip_ws": return repr(s.strip())
        return repr(getattr(s, method)(t))
    except ValueError as e:
        return "ValueError: %s" % e


def pad(method, s, width):
    return repr(s.zfill(width) if method == "zfill" else getattr(s, method)(width, "*"))



SOURCES = {
    "capitalize": "result = ('hELLO wORLD'.capitalize(), '\u01c6a'.capitalize(), ''.capitalize(), '1a'.capitalize())",
    "casefold": "result = ('Stra\xdfe'.casefold(), '\u03a3\u0391\u03a3'.casefold(), '\ufb01'.casefold())",
    "lower_upper": "result = ('\xc0b\xc7'.lower(), 'stra\xdfe'.upper(), '\ufb01'.upper(), '\u0130'.lower(), len('\u0130'.lower()))",
    "final_sigma": "result = ('\u03a3\u0391\u03a3'.lower(), '\u0391\u03a3 \u03a3'.lower(), '\u03a3'.lower())",
    "swapcase": "result = ('Hello \xdf'.swapcase(), '\u01c5'.swapcase())",
    "title": 'result = ("they\'re bill\'s friends".title(), \'hello1world\'.title(), \'\u01c6emal\'.title(), \'\xdfa\'.title())',
    "istitle": "result = ('Hello World'.istitle(), 'Hello world'.istitle(), ''.istitle(), '\u01c5'.istitle(), '1A'.istitle())",
    "isupper_islower": "result = ('ABC1'.isupper(), '1'.isupper(), 'abc'.islower(), 'aB'.islower(), '\u01c5'.isupper())",
    "isalpha_isalnum": "result = ('abc\xe9'.isalpha(), 'ab1'.isalpha(), ''.isalpha(), 'ab1\xb2'.isalnum(), 'a b'.isalnum())",
    "isascii": "result = (''.isascii(), 'abc\\x7f'.isascii(), '\xe9'.isascii())",
    "digit_classes": "result = [(c.isdecimal(), c.isdigit(), c.isnumeric()) for c in ('1', '\xb2', '\xbd', '\u0663', '\u216b', 'a')]",
    "isidentifier": "result = ('a1'.isidentifier(), '1a'.isidentifier(), 'def'.isidentifier(), '_'.isidentifier(), '\xe9'.isidentifier(), ''.isidentifier())",
    "isprintable": "result = ('ab c'.isprintable(), 'a\\n'.isprintable(), ''.isprintable(), '\\x7f'.isprintable(), '\\u00a0'.isprintable())",
    "isspace": "result = (' \\t\\n\\x0b\\x0c\\r\\x1c\\x85\\u2028'.isspace(), ''.isspace(), '\\u200b'.isspace())",
    "expandtabs": "result = ('01\\t012\\t0123\\t01234'.expandtabs(), '01\\t012\\t0123\\t01234'.expandtabs(4), 'a\\n\\tb'.expandtabs(2), 'a\\tb'.expandtabs(0), 'a\\tb'.expandtabs(-1))",
    "splitlines": "result = ('ab c\\n\\nde fg\\rkl\\r\\n'.splitlines(), 'ab c\\n\\nde fg\\rkl\\r\\n'.splitlines(keepends=True), ''.splitlines(), 'One line\\n'.splitlines())",
    "splitlines_boundaries": "result = 'a\\x0bb\\x0cc\\x1cd\\x1de\\x1ef\\x85g\\u2028h\\u2029i'.splitlines()",
    "split_vs_splitlines": "result = (''.split('\\n'), 'Two lines\\n'.split('\\n'))",
    "split_maxsplit": "result = ('1,2,3'.split(',', maxsplit=1), '1,2,,3,'.split(','), '   1   2   3   '.split(None, 1), '1<>2<>3<4'.split('<>'))",
    "rsplit_maxsplit": "result = ('1,2,3'.rsplit(',', 1), '  a b c  '.rsplit(maxsplit=1))",
    "split_bad_sep": "result = 'a'.split(1)",
    "join": "result = (', '.join(['a', 'b']), ''.join([]), '-'.join('abc'), 'x'.join(iter(('1',))))",
    "join_nonstr": "result = ''.join(['a', 1])",
    "join_bytes": "result = ''.join([b'a'])",
    "maketrans_dict": "result = str.maketrans({'a': '1', 98: None, 'c': 'xyz'})",
    "maketrans_three": "result = str.maketrans('ab', 'xy', 'c')",
    "maketrans_unequal": "result = str.maketrans('ab', 'x')",
    "maketrans_bad_key": "result = str.maketrans({'ab': 1})",
    "translate": "result = 'abcabd'.translate(str.maketrans({'a': '1', 'b': None, 'c': 'xyz'}))",
    "translate_lookup_error": "class T:\n    def __getitem__(self, k):\n        if k == 97: return 'A'\n        raise LookupError\nresult = 'abc'.translate(T())",
    "translate_bad_value": "result = 'a'.translate({97: 1.5})",
    "translate_ord_value": "result = 'a'.translate({97: 98})",
    "encode": "result = ('\xe9'.encode(), '\xe9'.encode('latin-1'), '\xe9'.encode('ascii', 'replace'), '\xe9'.encode('ascii', 'ignore'))",
    "encode_error": "result = '\xe9'.encode('ascii')",
    "encode_unknown": "result = 'a'.encode('nosuch')",
    "count_range": "result = ('aaaa'.count('a', 1, 3), 'aaaa'.count('', 1, 3), 'abab'.count('ab', -2), 'a'.count('', 5))",
    "find_range": "result = ('abcabc'.find('c', 3), 'abcabc'.find('c', 3, 5), 'abc'.find('', 4), 'abc'.find('', 3), 'abc'.rfind('', 1, 2))",
    "find_in_operator": "result = ('Py' in 'Python', '' in 'abc')",
    "index_error": "result = 'abc'.index('d')",
    "rindex_error": "result = 'abc'.rindex('d')",
    "startswith_tuple": "result = ('abc'.startswith(('x', 'ab')), 'abc'.endswith(('c',), 0, 2), 'abc'.startswith('', 3), 'abc'.startswith('', 4))",
    "startswith_bad": "result = 'abc'.startswith(['a'])",
    "startswith_tuple_bad": "result = 'abc'.startswith(('a', 1))",
    "strip_examples": "result = ('   spacious   '.strip(), 'www.example.com'.strip('cmowz.'), '#....... Section 3.2.1 Issue #32 .......'.strip('.#! '))",
    "lstrip_vs_removeprefix": "result = ('Arthur: three!'.lstrip('Arthur: '), 'Arthur: three!'.removeprefix('Arthur: '))",
    "strip_none": "result = '  a  '.strip(None)",
    "strip_bad": "result = 'a'.strip(1)",
    "replace_count_keyword": "result = ('aaa'.replace('a', 'b', count=2), 'aaa'.replace('a', 'b', -1), 'abc'.replace('', '-', 2))",
    "zfill_examples": "result = ('42'.zfill(5), '-42'.zfill(5), '+'.zfill(3), ''.zfill(2))",
    "center_bad_fill": "result = 'a'.center(5, 'ab')",
    "ljust_bad_fill": "result = 'a'.ljust(5, 1)",
    "center_index_width": "class W:\n    def __index__(self): return 4\nresult = 'a'.center(W(), '-')",
    "center_float_width": "result = 'a'.center(4.0)",
    "pad_unicode_fill": "result = 'a'.center(4, '\xe9')",
    "partition_bad": "result = 'a'.partition(None)",
    "str_no_args": 'result = str()',
    "str_object": 'result = (str(S()), str(NoStr()), str(1.5), str(None))',
    "str_bad_dunder": 'result = str(BadStr())',
    "str_bytes_repr": "result = str(b'Zoot!')",
    "str_decode": "result = (str(b'caf\\xc3\\xa9', 'utf-8'), str(b'caf\\xe9', 'latin-1'), str(bytearray(b'a'), errors='strict'), str(memoryview(b'ab'), 'ascii'))",
    "str_decode_error": "result = str(b'\\xff', 'utf-8')",
    "str_decode_replace": "result = str(b'a\\xffb', 'utf-8', 'replace')",
    "str_encoding_nonbytes": "result = str('a', 'utf-8')",
    "str_encoding_int": "result = str(1, 'utf-8')",
    "str_subclass_returns": "result = (type(str(Sub('a'))).__name__, type(Sub('a').upper()).__name__, type(Sub('a').strip()).__name__)",
    "index_char": "s = 'abc'\nresult = (s[0] == s[0:1], type(s[0]).__name__, s[-1], len(s[1]))",
    "immutable": "s = 'abc'\ns[0] = 'x'",
    "concat_literals": "result = ('spam ' 'eggs') == 'spam eggs'",
    "triple_quoted": "result = '''a\nb'''",
    "u_prefix": "result = u'abc' == 'abc'",
    "ur_prefix": 'compile("ur\'a\'", \'s\', \'eval\')',
    "code_points": "result = (len('\xe9'), len('e\\u0301'), [ord(c) for c in '\U0001f600a'])",
    "method_on_type": "result = (str.upper('a'), str.join('-', 'ab'))",
    "method_wrong_self": 'result = str.upper(1)',
    "too_many_args": "result = 'a'.upper(1)",
    "keyword_rejected": "result = 'a'.find(sub='a')",
    "format_map": "class Default(dict):\n    def __missing__(self, key): return key\nresult = '{name} was born in {country}'.format_map(Default(name='Guido'))"
}


TYPES = {name: value for name, value in list(globals().items()) if isinstance(value, type) and name[0].isupper()}


def generated(p):
    s = "".join(p["s"])
    if p["method"] in PAD:
        return pad(p["method"], s, p["width"])
    return search(p["method"], s, "".join(p.get("t", ())))


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
