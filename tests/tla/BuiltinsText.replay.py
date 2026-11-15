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
    "ascii_bad": 'result = ascii(BadRepr())',
    "str_bad": 'result = str(BadStr())',
    "repr_recursive": 'a = [1]\na.append(a)\nresult = repr(a)',
    "repr_bytes_quotes": 'result = (repr(b"\'"), repr(b\'"\'), repr(b\'\\\'"\'))',
    "format_hook": "result = (format(F(), 'x'), format(F()), f'{F():yz}')",
    "format_fields": "class G:\n    def __init__(s, n): s.n = n\n    def __format__(s, spec): return s.n + '<' + spec + '>'\n"
                     "class H:\n    def __init__(s): s.g = G('h')\n"
                     "result = '{0:{1}}|{x}|{2.g}|{3[0]}'.format(G('a'), G('b'), H(), [G('d')], x=G('c'))",
    "format_map_fields": "class G:\n    def __init__(s, n): s.n = n\n    def __format__(s, spec): return s.n + '<' + spec + '>'\n"
                         "def positional():\n    try: return '{}'.format_map({})\n    except ValueError as e: return 'ValueError: ' + str(e)\n"
                         "result = (str.format('{}|{k:x}', G('a'), k=G('b')), '{k}'.format_map({'k': G('c')}), positional())",
    "ascii_container_calls": "log = []\nclass S:\n    def __init__(s, t): s.t = t\n    def __repr__(s):\n        for _ in (): pass\n        log.append(s.t)\n        return s.t\n"
                             "result = (ascii([S('a'), (S('\\xe9'),)]), len(log))",
    "object_format_calls": "log = []\nclass S:\n    def __str__(s):\n        for _ in (): pass\n        log.append('str')\n        return 's'\n"
                           "f = object.__format__\nresult = (object.__format__(S(), ''), f(S(), ''), log)",
    "format_object_spec": "result = format(object(), 'x')",
    "format_object_empty": "result = format(object(), '')[:8]",
    "format_bad_return": 'result = format(BadFormat())',
    "format_spec_type": 'result = format(1, 2)',
    "print_starred": "log = []\nclass S:\n    def __init__(s, v): s.v = v\n    def __str__(s):\n        for _ in (): pass\n        log.append('str %d' % s.v)\n        return 's%d' % s.v\n"
                     "w = W()\nprint(*[S(1), 2, S(3)], sep='-', end='.', file=w)\nresult = (w.parts, log)",
    "print_sep_end": "w = W()\nprint(1, 'a', None, sep='|', end='!\\n', file=w)\nresult = w.parts",
    "print_none_sep": 'w = W()\nprint(1, 2, sep=None, end=None, file=w)\nresult = w.parts',
    "print_no_args": 'w = W()\nprint(file=w)\nresult = w.parts',
    "print_flush": "w = W()\nprint('x', file=w, flush=True)\nresult = w.flushed",
    "print_bad_sep": 'print(1, sep=1)',
    "print_bad_end": "print(1, end=b'')",
    "print_file_none_ok": "result = print(end='', file=None) is None",
    "str_base_repr": "class R(int):\n    def __repr__(s): return 'R!'\nclass S(int):\n    def __str__(s): return 'S!'\n"
                     "result = (str(R(1)), f'{R(2)}', format(R(3), ''), format(R(3), 'd'), format(S(4), ''))",
    "print_file_getattr": "log = []\nclass G:\n    def __getattr__(s, name):\n        for _ in (): pass\n        log.append(name)\n"
                          "        return lambda *a: log.extend(a)\nclass P:\n    @property\n    def write(s):\n        log.append('get')\n        return log.append\n"
                          "print('a', 1, sep='-', file=G(), flush=True)\nprint('b', file=P())\nresult = log",
    "print_file_nowrite": 'print(1, file=1)',
    "print_unknown_kw": 'print(1, x=1)',
    "repr_nested_items": "log = []\nclass Q:\n    def __init__(self, t): self.t = t\n    def __repr__(self):\n        for _ in range(2): pass\n        log.append(self.t); return self.t\n"
                         "result = (repr([Q('a'), [Q('b'), (Q('c'),)]]), str(([Q('d')],)), log)",
    "repr_map_items": "log = []\nclass Q:\n    def __init__(self, t): self.t = t\n    def __repr__(self):\n        for _ in range(2): pass\n        log.append(self.t); return self.t\n"
                      "result = (repr({Q('a'): Q('b'), 1: [Q('c')]}), str({Q('d')}), repr(frozenset([Q('e')])), log)",
    "print_str_calls": "w = W()\nclass S:\n    def __str__(self): return 'S!'\nprint(S(), file=w)\nresult = w.parts",
    "print_write_each": "log = []\nclass S:\n    def __str__(self):\n        for _ in (): pass\n        log.append('str'); return 's'\n"
                        "class G:\n    def __getattr__(self, name):\n        for _ in (): pass\n        log.append('get'); return lambda t: None\n"
                        "print(S(), 1, S(), file=G())\nresult = log",
    "print_str_sep": "w = W()\nclass M(str):\n    def __str__(self):\n        for _ in (): pass\n        return '+'\n"
                     "print(1, 2, sep=M('-'), end=M('!'), file=w)\nresult = w.parts",
    "str_bytes_warns_not": "result = str(b'ab')",
    "repr_str_quotes": 'result = (repr("it\'s"), repr(\'say "hi"\'), repr(\'both \\\' "\'))',
    "repr_nonprintable": "result = (repr('\\x00\\x1f\\x7f\\x80\\xa0\\xad'), repr('\\u2028'), repr('\\ud800'))",
    "isprintable_rule": "result = ('\\xe9'.isprintable(), '\\u2028'.isprintable(), ' '.isprintable(), '\\xa0'.isprintable())",
    "format_width_unicode": "result = format('\\u03b1', '*^5')",
    "ascii_bytes_unchanged": "result = ascii(b'\\xff')",
    "bin_format_spec": "result = (format(10, 'b'), format(10, '#x'), format(255, '_b'))",
    "repr_own_slot": "result = ([type(v).__repr__(v) == repr(v) for v in (len, [].append, str.join, str.__add__, (1).__add__)], "
                     "b'a'.__str__())",
    "repr_subclass_own": "class I(int):\n    def __repr__(self): return 'I!'\nclass J(int):\n    def __str__(self): return 'J!'\n"
                         "result = (repr(I(1)), str(I(1)), format(I(1)), format(I(1), 'd'), repr(J(2)), str(J(2)))",
    "repr_metaclass": "class M(type):\n    def __repr__(cls): return 'M:' + cls.__name__\nclass C(metaclass=M): pass\n"
                      "result = (repr(C), str(C), format(C), '%s' % (C,))",
    "repr_items_own": "class I(int):\n    def __repr__(self): return 'I!'\n"
                      "class M(type):\n    def __repr__(cls): return 'M:' + cls.__name__\nclass C(metaclass=M): pass\n"
                      "result = (repr([I(1), C]), str({I(2): (C,)}), f'{[C]}')",
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
