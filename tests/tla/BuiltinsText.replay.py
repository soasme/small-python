# Replays BuiltinsText.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
POINTS = [0x41, 0x27, 0x22, 0x5c, 0x0a, 0x09, 0x7f, 0xe9, 0x3b1, 0x1f600]
STRINGS = [()] + [(a,) for a in POINTS] + [(a, b) for a in POINTS for b in POINTS]


def text(op, s):
    s = "".join(map(chr, s))
    if op == "ascii": return ascii(s)
    if op == "repr_len": return repr(len(repr(s)))
    if op == "ord": return repr([ord(c) for c in s])
class W:
    def __init__(self): self.parts = []; self.flushed = 0
    def write(self, s): self.parts.append(s)
    def flush(self): self.flushed += 1
class F:
    def __format__(self, spec): return "F<" + spec + ">"
class BadRepr:
    def __repr__(self): return 1
class BadStr:
    def __str__(self): return b"x"
class U:
    def __repr__(self): return "\u03b1"
class BadFormat:
    def __format__(self, spec): return 1

SOURCES = {
    "chr_bounds": "result = (chr(0), chr(0x10ffff) == '\\U0010ffff', ord(chr(0x10ffff)))",
    "chr_over": 'result = chr(0x110000)',
    "chr_negative": 'result = chr(-1)',
    "chr_float": 'result = chr(65.0)',
    "chr_huge": 'result = chr(2 ** 64)',
    "ord_long": "result = ord('ab')",
    "ord_empty": "result = ord('')",
    "ord_bytes": "result = (ord(b'a'), ord(bytearray(b'b')))",
    "ord_int": 'result = ord(1)',
    "ascii_object": "result = (ascii(U()), repr(U()) == '\\u03b1', ascii([U()]))",
    "repr_bad": 'result = repr(BadRepr())',
    "str_bad": 'result = str(BadStr())',
    "repr_recursive": 'a = [1]\na.append(a)\nresult = repr(a)',
    "repr_bytes_quotes": 'result = (repr(b"\'"), repr(b\'"\'), repr(b\'\\\'"\'))',
    "format_hook": "result = (format(F(), 'x'), format(F()), f'{F():yz}')",
    "format_object_spec": "result = format(object(), 'x')",
    "format_object_empty": "result = format(object(), '')[:8]",
    "format_bad_return": 'result = format(BadFormat())',
    "format_spec_type": 'result = format(1, 2)',
    "print_sep_end": "w = W()\nprint(1, 'a', None, sep='|', end='!\\n', file=w)\nresult = w.parts",
    "print_none_sep": 'w = W()\nprint(1, 2, sep=None, end=None, file=w)\nresult = w.parts',
    "print_no_args": 'w = W()\nprint(file=w)\nresult = w.parts',
    "print_flush": "w = W()\nprint('x', file=w, flush=True)\nresult = w.flushed",
    "print_bad_sep": 'print(1, sep=1)',
    "print_bad_end": "print(1, end=b'')",
    "print_file_none_ok": "result = print(end='', file=None) is None",
    "print_file_nowrite": 'print(1, file=1)',
    "print_unknown_kw": 'print(1, x=1)',
    "print_str_calls": "w = W()\nclass S:\n    def __str__(self): return 'S!'\nprint(S(), file=w)\nresult = w.parts",
    "str_bytes_warns_not": "result = str(b'ab')",
    "repr_str_quotes": 'result = (repr("it\'s"), repr(\'say "hi"\'), repr(\'both \\\' "\'))',
    "repr_nonprintable": "result = (repr('\\x00\\x1f\\x7f\\x80\\xa0\\xad'), repr('\\u2028'), repr('\\ud800'))",
    "isprintable_rule": "result = ('\\xe9'.isprintable(), '\\u2028'.isprintable(), ' '.isprintable(), '\\xa0'.isprintable())",
    "format_width_unicode": "result = format('\\u03b1', '*^5')",
    "ascii_bytes_unchanged": "result = ascii(b'\\xff')",
    "bin_format_spec": "result = (format(10, 'b'), format(10, '#x'), format(255, '_b'))"
}


TYPES = {name: value for name, value in list(globals().items()) if isinstance(value, type) and name[0].isupper()}


def generated(p):
    return text(p["op"], p["s"])


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
